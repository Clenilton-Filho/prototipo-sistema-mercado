from datetime import datetime

# Sistema simples em memória para um mercado (uso interno por funcionários)
# Arquitetura: um único arquivo para facilitar entendimento de iniciantes.
# Banco de dados em memória: dicionários e listas.


class BancoMemoria:
    """Banco em memória. Estruturas simples:
    - products: {product_id: {name, code, price, discount_near_expiry, near_days}}
    - suppliers: {supplier_id: {name, products: {product_id: price}}}
    - batches: list of {id, product_id, supplier_id, quantity, expiry: date}
    - deliverers: {id: {name}}
    """

    def __init__(self):
        self.produtos = {}
        self.fornecedores = {}
        self.lotes = []
        self.entregas = []
        self.entregadores = {}
        self._pid = 1
        self._sid = 1
        self._bid = 1
        self._did = 1

    # Produtos
    def adicionar_produto(self, name, code, price, discount_near_expiry=0.0, near_days=7):
        # validações simples: nome e código únicos
        for p in self.produtos.values():
            if p['nome'].lower() == name.lower():
                raise ValueError('Nome de produto já existe')
            if p['codigo'] == code:
                raise ValueError('Código do produto já existe')
        pid = self._pid
        self.produtos[pid] = {
            'id': pid,
            'nome': name,
            'codigo': code,
            'preco': float(price),
            'desconto_perto_vencimento': float(discount_near_expiry),
            'dias_perto': int(near_days)
        }
        self._pid += 1
        return pid

    def atualizar_produto(self, product_id, name, code, price, discount_near_expiry=0.0, near_days=7):
        # update_product: atualiza os campos de um produto existente.
        # - valida unicidade de `name` e `code` entre os demais produtos
        # - converte valores para os tipos corretos
        # Usado pela UI quando o usuário edita um produto e clica em
        # "Salvar alterações" no formulário de cadastro.
        # atualiza um produto existente, mantendo validações de unicidade
        if product_id not in self.produtos:
            raise ValueError('Produto não encontrado')
        for pid, p in self.produtos.items():
            if pid == product_id:
                continue
            if p['nome'].lower() == name.lower():
                raise ValueError('Nome de produto já existe')
            if p['codigo'] == code:
                raise ValueError('Código do produto já existe')
        self.produtos[product_id].update({
            'nome': name,
            'codigo': code,
            'preco': float(price),
            'desconto_perto_vencimento': float(discount_near_expiry),
            'dias_perto': int(near_days)
        })

    def remover_produto(self, product_id):
        # remove_product: remove o produto do banco em memória e
        # limpa referências simples (ex.: preços em fornecedores).
        # Usado pela UI quando o usuário clica no ícone de lixeira na
        # tabela de produtos.
        # remove produto e quaisquer referências simples
        if product_id in self.produtos:
            del self.produtos[product_id]
            # remover preços em fornecedores que referenciam este produto
            for s in self.fornecedores.values():
                if product_id in s.get('produtos', {}):
                    try:
                        del s['produtos'][product_id]
                    except Exception:
                        pass

    # Fornecedores
    def adicionar_fornecedor(self, name):
        for s in self.fornecedores.values():
            if s['nome'].lower() == name.lower():
                raise ValueError('Nome de fornecedor já existe')
        sid = self._sid
        self.fornecedores[sid] = {'id': sid, 'nome': name, 'produtos': {}}
        self._sid += 1
        return sid

    def fornecedor_definir_preco(self, supplier_id, product_id, price):
        self.fornecedores[supplier_id]['produtos'][product_id] = float(price)

    # Lotes / estoque
    def adicionar_lote(self, product_id, supplier_id, quantity, expiry_date_str):
        bid = self._bid
        expiry = None
        try:
            expiry = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
        except Exception:
            expiry = None
        self.lotes.append({
            'id': bid,
            'produto_id': product_id,
            'fornecedor_id': supplier_id,
            'quantidade': int(quantity),
            'vencimento': expiry,
            'vencimento_raw': expiry_date_str,
        })
        self._bid += 1
        return bid

    def remover_lote(self, batch_id):
        self.lotes = [b for b in self.lotes if b['id'] != batch_id]

    def atualizar_lote(self, batch_id, product_id, supplier_id, quantity, expiry_date_str):
        # update_batch: atualiza os dados de um lote (batch).
        # Converte a data de string para `date` quando possível e
        # sobrescreve os campos do lote correspondente.
        # Usado pela UI ao editar um lote e salvar alterações.
        # atualiza um lote existente
        expiry = None
        try:
            expiry = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
        except Exception:
            expiry = None
        for b in self.lotes:
            if b['id'] == batch_id:
                b['produto_id'] = product_id
                b['fornecedor_id'] = supplier_id
                b['quantidade'] = int(quantity)
                b['vencimento'] = expiry
                b['vencimento_raw'] = expiry_date_str
                return

    # Entregadores
    def adicionar_entregador(self, name):
        for d in self.entregadores.values():
            if d['nome'].lower() == name.lower():
                raise ValueError('Nome de entregador já existe')
        did = self._did
        self.entregadores[did] = {'id': did, 'nome': name}
        self._did += 1
        return did

    def atualizar_entregador(self, deliverer_id, name):
        # update_deliverer: atualiza o nome de um entregador,
        # garantindo que não haja duplicatas.
        # Usado pela UI quando o usuário edita um entregador e salva.
        # atualiza nome do entregador com validação de unicidade
        if deliverer_id not in self.entregadores:
            raise ValueError('Entregador não encontrado')
        for did, d in self.entregadores.items():
            if did == deliverer_id:
                continue
            if d['nome'].lower() == name.lower():
                raise ValueError('Nome de entregador já existe')
        self.entregadores[deliverer_id]['nome'] = name

    def adicionar_entrega(self, deliverer_id, total):
        # adiciona entrega pendente para o entregador
        did = len(self.entregas) + 1
        self.entregas.append({'id': did, 'entregador_id': deliverer_id, 'valor_total': float(total), 'status': 'pending'})
        return did

    def contar_entregas_para(self, deliverer_id):
        return sum(1 for d in self.entregas if d['entregador_id'] == deliverer_id and d['status'] == 'pending')

    # estoque atual calculado a partir dos lotes
    def estoque_atual(self):
        stock = {}
        for b in self.lotes:
            pid = b['produto_id']
            stock[pid] = stock.get(pid, 0) + b['quantidade']
        return stock

    def produtos_vencidos(self):
        today = datetime.today().date()
        expired = []
        for b in self.lotes:
            if b['vencimento'] and b['vencimento'] < today and b['quantidade'] > 0:
                expired.append(b)
        return expired

    def produtos_perto_vencimento(self):
        today = datetime.today().date()
        near = []
        for b in self.lotes:
            if b['vencimento']:
                prod = self.produtos.get(b['produto_id'])
                ndays = prod.get('dias_perto', 7)
                if 0 <= (b['vencimento'] - today).days <= ndays:
                    near.append(b)
        return near
