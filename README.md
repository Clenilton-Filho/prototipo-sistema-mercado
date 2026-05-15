Projeto Mercado - Protótipo

Resumo curto:
- Interface desktop construída com Flet para uso interno (funcionários/operadores).
- Persistência completa em SQLite (`data/mercado.db`) via `banco_SQLITE.py`.

Funcionalidades incluídas
- Autenticação: modal de login/registro; registro exige a "senha do estabelecimento" (seed criada na primeira execução). Senhas armazenadas com PBKDF2-HMAC-SHA256 + salt para segurança.
- Caixa: adicionar itens ao carrinho, aplicar descontos automáticos para lotes perto do vencimento, finalizar venda com débito de lotes em ordem de vencimento e registro de entrega.
- Gestão de Produtos: CRUD de produtos, configuração de desconto para proximidade de vencimento.
- Gestão de Fornecedores: CRUD de fornecedores e atribuição/edição de preços por produto.
- Gestão de Lotes/Estoque: registro de lotes com quantidade e vencimento; lotes são removidos por ordem de vencimento ao finalizar vendas.
- Entregadores/Entregas: cadastro de entregadores e registro de entregas pendentes.
- Relatórios: listas de lotes vencidos e lotes próximos do vencimento.
- UX/Compatibilidade: tabelas roláveis, sanitização de letras e outros em tempo real para campos numéricos.

Arquivos principais
- Ponto de entrada: [main.py](main.py)
- Inicialização e navegação: [views/app.py](views/app.py)
- Camada de persistência em banco: [banco_SQLITE.py](banco_SQLITE.py)
- Modais/overlays: [views/overlay.py](views/overlay.py)
- Views/telas: [views/caixa.py](views/caixa.py), [views/produtos.py](views/produtos.py), [views/fornecedores.py](views/fornecedores.py), [views/lotes.py](views/lotes.py), [views/entregadores.py](views/entregadores.py), [views/relatorios.py](views/relatorios.py), [views/auth.py](views/auth.py)

Detalhes de implementação relevantes
- Senha do estabelecimento: gerada automaticamente como `salt$hash` e armazenada em `settings` na DB. Seed padrão (apenas protótipo): `mercadoDaPraça@123`.
- Hashing de informações de usuários: PBKDF2-HMAC-SHA256 com salt.
- Estoque: duas funções úteis em `banco_SQLITE.py`: `estoque_atual()` e `estoque_disponivel()` (ignora lotes vencidos).
- Descontos por proximidade: calculados no Caixa lendo `desconto_perto_vencimento` e `dias_perto` do produto.

Como executar
1. Criar/ativar venv (Windows PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Instalar dependências:

```powershell
pip install -r requirements.txt
```

3. Executar:

```powershell
flet run main.py
```

Notas e recomendações
- Testes rápidos: ao abrir a aplicação, registre um usuário usando a senha do estabelecimento (seed) ou redefina removendo `data/mercado.db` para regenerar o seed.
- Verifique a tela `Caixa` ao adicionar produtos e finalizar venda para confirmar débito de lotes e aplicação de descontos.

Requisitos
- Python 3.9+
- Dependências: [requirements.txt](requirements.txt) (principal: `flet`)