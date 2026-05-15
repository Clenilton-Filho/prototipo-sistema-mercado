from datetime import datetime
import hashlib
import os
import binascii
import sqlite3
from pathlib import Path


class BancoMemoria:
    """
    Implementação baseada exclusivamente em SQLite para persistência.

    Observações importantes:
    - O nome `BancoMemoria` foi mantido para compatibilidade com o
      restante do código (views), mas agora todas as leituras e
      escritas são feitas diretamente no arquivo SQLite `data/mercado.db`.
    - Esta versão evita caches permanentes em memória para reduzir
      inconsistências e simplificar o modelo de persistência.
    - As propriedades `produtos`, `fornecedores`, `lotes`, `entregadores`
      e `entregas` retornam estruturas no formato esperado pelas views.
    """

    def __init__(self):
        # caminho do banco em disco (criado automaticamente)
        self._data_dir = Path(__file__).parent
        self._db_path = self._data_dir / 'data' / 'mercado.db'
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._db_path))
        self._conn.row_factory = sqlite3.Row
        self._ensure_tables()

    def _normalize_code(self, code: str):
        """Normalize o código do produto: retorna `None` se vazia, string limpa caso contrário."""
        if code is None:
            return None
        c = str(code).strip()
        return c if c != '' else None

    def _hash_password(self, password: str, salt: bytes) -> str:
        """Gera hash seguro para uma senha usando PBKDF2-HMAC-SHA256."""
        dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return binascii.hexlify(dk).decode('ascii')

    def _ensure_tables(self):
        """Cria as tabelas necessárias caso não existam.

        Tabelas criadas: users, settings, products, suppliers,
        supplier_products, batches, deliverers, deliveries.
        """
        cur = self._conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                salt TEXT NOT NULL,
                pwd TEXT NOT NULL
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        # tabelas de domínio
        cur.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                codigo TEXT UNIQUE,
                preco REAL,
                desconto_perto_vencimento REAL DEFAULT 0,
                dias_perto INTEGER DEFAULT 7
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT UNIQUE
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS supplier_products (
                supplier_id INTEGER,
                product_id INTEGER,
                price REAL,
                PRIMARY KEY (supplier_id, product_id)
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS batches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                produto_id INTEGER,
                fornecedor_id INTEGER,
                quantidade INTEGER,
                vencimento_raw TEXT
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS deliverers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT UNIQUE
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS deliveries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entregador_id INTEGER,
                valor_total REAL,
                status TEXT
            )
        ''')
        self._conn.commit()

        # seed: senha do estabelecimento para permitir registro inicial
        cur.execute("SELECT value FROM settings WHERE key = 'establishment_password'")
        row = cur.fetchone()
        if not row:
            default = 'mercadoDaPraça@123'  # protótipo
            salt = os.urandom(16)
            pwd_hash = self._hash_password(default, salt)
            combined = f"{binascii.hexlify(salt).decode('ascii')}${pwd_hash}"
            cur.execute("INSERT INTO settings(key, value) VALUES(?,?)", ('establishment_password', combined))
            self._conn.commit()

    # ------------------ Autenticação ------------------
    def usuario_existe(self, username: str) -> bool:
        """Retorna True se o usuário existir no banco."""
        cur = self._conn.cursor()
        cur.execute('SELECT 1 FROM users WHERE username = ?', (username,))
        return cur.fetchone() is not None

    def adicionar_usuario(self, username: str, password: str):
        """Cria um novo usuário com salt e hash armazenados no DB.

        Lança ValueError em caso de entradas inválidas ou usuário já existente.
        """
        if not username or not password:
            raise ValueError('Usuário e senha são obrigatórios')
        cur = self._conn.cursor()
        salt = os.urandom(16)
        pwd_hash = self._hash_password(password, salt)
        try:
            cur.execute('INSERT INTO users(username, salt, pwd) VALUES(?,?,?)', (username, binascii.hexlify(salt).decode('ascii'), pwd_hash))
            self._conn.commit()
            return True
        except sqlite3.IntegrityError:
            raise ValueError('Usuário já existe')

    def autenticar_usuario(self, username: str, password: str) -> bool:
        """Verifica credenciais comparando o hash armazenado."""
        cur = self._conn.cursor()
        cur.execute('SELECT salt, pwd FROM users WHERE username = ?', (username,))
        row = cur.fetchone()
        if not row:
            return False
        try:
            salt = binascii.unhexlify(row['salt'])
        except Exception:
            return False
        return self._hash_password(password, salt) == row['pwd']

    def verificar_senha_estabelecimento(self, password: str) -> bool:
        """Verifica a senha do estabelecimento (armazenada em `settings`)."""
        cur = self._conn.cursor()
        cur.execute("SELECT value FROM settings WHERE key = 'establishment_password'")
        row = cur.fetchone()
        if not row or not row['value']:
            return False
        try:
            salt_hex, pwd_hash = row['value'].split('$', 1)
            salt = binascii.unhexlify(salt_hex)
        except Exception:
            return False
        return self._hash_password(password, salt) == pwd_hash

    # ------------------ Leitura (propriedades) ------------------
    @property
    def produtos(self):
        """Retorna dict de produtos no formato esperado pelas views."""
        cur = self._conn.cursor()
        cur.execute('SELECT id, nome, codigo, preco, desconto_perto_vencimento, dias_perto FROM products')
        rows = cur.fetchall()
        return {r['id']: {'id': r['id'], 'nome': r['nome'], 'codigo': r['codigo'] if r['codigo'] is not None else '', 'preco': float(r['preco']) if r['preco'] is not None else 0.0, 'desconto_perto_vencimento': float(r['desconto_perto_vencimento']) if r['desconto_perto_vencimento'] is not None else 0.0, 'dias_perto': int(r['dias_perto']) if r['dias_perto'] is not None else 7} for r in rows}

    @property
    def fornecedores(self):
        """Retorna dict de fornecedores com preços por produto."""
        cur = self._conn.cursor()
        cur.execute('SELECT id, nome FROM suppliers')
        suppliers = {r['id']: {'id': r['id'], 'nome': r['nome'], 'produtos': {}} for r in cur.fetchall()}
        cur.execute('SELECT supplier_id, product_id, price FROM supplier_products')
        for r in cur.fetchall():
            sid = r['supplier_id']
            pid = r['product_id']
            price = float(r['price']) if r['price'] is not None else 0.0
            if sid in suppliers:
                suppliers[sid]['produtos'][pid] = price
        return suppliers

    @property
    def lotes(self):
        """Lista de lotes com campos `vencimento` já convertidos quando possível."""
        cur = self._conn.cursor()
        cur.execute('SELECT id, produto_id, fornecedor_id, quantidade, vencimento_raw FROM batches')
        res = []
        for r in cur.fetchall():
            venc = None
            try:
                if r['vencimento_raw']:
                    venc = datetime.strptime(r['vencimento_raw'], '%Y-%m-%d').date()
            except Exception:
                venc = None
            res.append({'id': r['id'], 'produto_id': r['produto_id'], 'fornecedor_id': r['fornecedor_id'], 'quantidade': int(r['quantidade']) if r['quantidade'] is not None else 0, 'vencimento': venc, 'vencimento_raw': r['vencimento_raw']})
        return res

    @property
    def entregadores(self):
        cur = self._conn.cursor()
        cur.execute('SELECT id, nome FROM deliverers')
        return {r['id']: {'id': r['id'], 'nome': r['nome']} for r in cur.fetchall()}

    @property
    def entregas(self):
        cur = self._conn.cursor()
        cur.execute('SELECT id, entregador_id, valor_total, status FROM deliveries')
        return [{'id': r['id'], 'entregador_id': r['entregador_id'], 'valor_total': float(r['valor_total']) if r['valor_total'] is not None else 0.0, 'status': r['status']} for r in cur.fetchall()]

    # ------------------ CRUDs que persistem no DB ------------------
    def adicionar_produto(self, name, code, price, discount_near_expiry=0.0, near_days=7):
        """Insere um produto no DB; valida unicidade de nome/código."""
        cur = self._conn.cursor()
        code = self._normalize_code(code)
        # apenas verifique equality de código quando um código foi informado
        cur.execute('SELECT id FROM products WHERE lower(nome)=? OR (? IS NOT NULL AND codigo = ?)', (name.lower(), code, code))
        if cur.fetchone():
            raise ValueError('Nome ou código do produto já existe')
        cur.execute('INSERT INTO products(nome, codigo, preco, desconto_perto_vencimento, dias_perto) VALUES(?,?,?,?,?)',
                    (name, code, float(price), float(discount_near_expiry), int(near_days)))
        self._conn.commit()
        return cur.lastrowid

    def atualizar_produto(self, product_id, name, code, price, discount_near_expiry=0.0, near_days=7):
        """Atualiza campos de um produto existente."""
        cur = self._conn.cursor()
        cur.execute('SELECT id FROM products WHERE id=?', (product_id,))
        if not cur.fetchone():
            raise ValueError('Produto não encontrado')
        code = self._normalize_code(code)
        # verificar unicidade: comparar nome sempre, comparar código só se informado
        cur.execute('SELECT id FROM products WHERE (lower(nome)=? OR (? IS NOT NULL AND codigo=?)) AND id<>?', (name.lower(), code, code, product_id))
        if cur.fetchone():
            raise ValueError('Nome ou código do produto já existe')
        cur.execute('UPDATE products SET nome=?, codigo=?, preco=?, desconto_perto_vencimento=?, dias_perto=? WHERE id=?', (name, code, float(price), float(discount_near_expiry), int(near_days), product_id))
        self._conn.commit()

    def remover_produto(self, product_id):
        """Remove produto e referências relacionadas (preços, lotes)."""
        cur = self._conn.cursor()
        cur.execute('DELETE FROM supplier_products WHERE product_id = ?', (product_id,))
        cur.execute('DELETE FROM products WHERE id = ?', (product_id,))
        cur.execute('DELETE FROM batches WHERE produto_id = ?', (product_id,))
        self._conn.commit()

    def adicionar_fornecedor(self, name):
        """Insere fornecedor; nome deve ser único."""
        cur = self._conn.cursor()
        cur.execute('SELECT id FROM suppliers WHERE lower(nome)=?', (name.lower(),))
        if cur.fetchone():
            raise ValueError('Nome de fornecedor já existe')
        cur.execute('INSERT INTO suppliers(nome) VALUES(?)', (name,))
        self._conn.commit()
        return cur.lastrowid

    def atualizar_fornecedor(self, supplier_id, name):
        """Atualiza o nome de um fornecedor existente, garantindo unicidade."""
        cur = self._conn.cursor()
        cur.execute('SELECT id FROM suppliers WHERE id=?', (supplier_id,))
        if not cur.fetchone():
            raise ValueError('Fornecedor não encontrado')
        cur.execute('SELECT id FROM suppliers WHERE lower(nome)=? AND id<>?', (name.lower(), supplier_id))
        if cur.fetchone():
            raise ValueError('Nome de fornecedor já existe')
        cur.execute('UPDATE suppliers SET nome=? WHERE id=?', (name, supplier_id))
        self._conn.commit()

    def remover_fornecedor(self, supplier_id):
        """Remove um fornecedor e as referências de preços associadas."""
        cur = self._conn.cursor()
        cur.execute('DELETE FROM supplier_products WHERE supplier_id = ?', (supplier_id,))
        cur.execute('DELETE FROM suppliers WHERE id = ?', (supplier_id,))
        self._conn.commit()

    def fornecedor_definir_preco(self, supplier_id, product_id, price):
        """Atribui/atualiza preço de um produto para um fornecedor (upsert)."""
        cur = self._conn.cursor()
        cur.execute('REPLACE INTO supplier_products(supplier_id, product_id, price) VALUES(?,?,?)', (supplier_id, product_id, float(price)))
        self._conn.commit()

    def adicionar_lote(self, product_id, supplier_id, quantity, expiry_date_str):
        """Adiciona lote (registro de estoque) associado a um produto/fornecedor."""
        cur = self._conn.cursor()
        cur.execute('INSERT INTO batches(produto_id, fornecedor_id, quantidade, vencimento_raw) VALUES(?,?,?,?)', (product_id, supplier_id, int(quantity), expiry_date_str))
        self._conn.commit()
        return cur.lastrowid

    def remover_lote(self, batch_id):
        cur = self._conn.cursor()
        cur.execute('DELETE FROM batches WHERE id = ?', (batch_id,))
        self._conn.commit()

    def atualizar_lote(self, batch_id, product_id, supplier_id, quantity, expiry_date_str):
        cur = self._conn.cursor()
        cur.execute('UPDATE batches SET produto_id=?, fornecedor_id=?, quantidade=?, vencimento_raw=? WHERE id=?', (product_id, supplier_id, int(quantity), expiry_date_str, batch_id))
        self._conn.commit()

    def adicionar_entregador(self, name):
        cur = self._conn.cursor()
        cur.execute('SELECT id FROM deliverers WHERE lower(nome)=?', (name.lower(),))
        if cur.fetchone():
            raise ValueError('Nome de entregador já existe')
        cur.execute('INSERT INTO deliverers(nome) VALUES(?)', (name,))
        self._conn.commit()
        return cur.lastrowid

    def atualizar_entregador(self, deliverer_id, name):
        cur = self._conn.cursor()
        cur.execute('SELECT id FROM deliverers WHERE id=?', (deliverer_id,))
        if not cur.fetchone():
            raise ValueError('Entregador não encontrado')
        cur.execute('SELECT id FROM deliverers WHERE lower(nome)=? AND id<>?', (name.lower(), deliverer_id))
        if cur.fetchone():
            raise ValueError('Nome de entregador já existe')
        cur.execute('UPDATE deliverers SET nome=? WHERE id=?', (name, deliverer_id))
        self._conn.commit()

    def adicionar_entrega(self, deliverer_id, total):
        cur = self._conn.cursor()
        cur.execute('INSERT INTO deliveries(entregador_id, valor_total, status) VALUES(?,?,?)', (deliverer_id, float(total), 'pending'))
        self._conn.commit()
        return cur.lastrowid

    def contar_entregas_para(self, deliverer_id):
        cur = self._conn.cursor()
        cur.execute('SELECT COUNT(1) as cnt FROM deliveries WHERE entregador_id=? AND status=?', (deliverer_id, 'pending'))
        r = cur.fetchone()
        return int(r['cnt']) if r else 0

    # estoque atual calculado a partir dos lotes
    def estoque_atual(self):
        """Retorna dict {produto_id: quantidade_total} calculado pelo DB."""
        cur = self._conn.cursor()
        cur.execute('SELECT produto_id, SUM(quantidade) as total FROM batches GROUP BY produto_id')
        res = {}
        for r in cur.fetchall():
            res[r['produto_id']] = int(r['total']) if r['total'] is not None else 0
        return res

    def estoque_disponivel(self):
        """Retorna dict {produto_id: quantidade_disponivel} ignorando lotes vencidos.

        Considera disponíveis apenas lotes com `vencimento_raw` nulo ou maior/igual à data atual.
        """
        cur = self._conn.cursor()
        # usa função date('now') do SQLite para comparar datas em formato YYYY-MM-DD
        cur.execute("SELECT produto_id, SUM(quantidade) as total FROM batches WHERE vencimento_raw IS NULL OR date(vencimento_raw) >= date('now') GROUP BY produto_id")
        res = {}
        for r in cur.fetchall():
            res[r['produto_id']] = int(r['total']) if r['total'] is not None else 0
        return res

    def produtos_vencidos(self):
        """Retorna a lista de lotes cujo vencimento já passou."""
        today = datetime.today().date()
        cur = self._conn.cursor()
        cur.execute("SELECT id, produto_id, fornecedor_id, quantidade, vencimento_raw FROM batches WHERE vencimento_raw IS NOT NULL")
        expired = []
        for r in cur.fetchall():
            try:
                venc = datetime.strptime(r['vencimento_raw'], '%Y-%m-%d').date()
            except Exception:
                continue
            if venc < today and (r['quantidade'] or 0) > 0:
                expired.append({'id': r['id'], 'produto_id': r['produto_id'], 'fornecedor_id': r['fornecedor_id'], 'quantidade': int(r['quantidade']), 'vencimento': venc, 'vencimento_raw': r['vencimento_raw']})
        return expired

    def produtos_perto_vencimento(self):
        """Retorna lotes que estão dentro da janela de 'perto de vencer' do produto."""
        today = datetime.today().date()
        cur = self._conn.cursor()
        cur.execute('SELECT b.id, b.produto_id, b.fornecedor_id, b.quantidade, b.vencimento_raw, p.desconto_perto_vencimento, p.dias_perto FROM batches b JOIN products p ON p.id = b.produto_id')
        near = []
        for r in cur.fetchall():
            try:
                venc = datetime.strptime(r['vencimento_raw'], '%Y-%m-%d').date()
            except Exception:
                continue
            ndays = int(r['dias_perto']) if r['dias_perto'] is not None else 7
            if 0 <= (venc - today).days <= ndays:
                near.append({'id': r['id'], 'produto_id': r['produto_id'], 'fornecedor_id': r['fornecedor_id'], 'quantidade': int(r['quantidade']), 'vencimento': venc, 'vencimento_raw': r['vencimento_raw'], 'desconto_perto_vencimento': float(r['desconto_perto_vencimento']) if r['desconto_perto_vencimento'] is not None else 0.0})
        return near
