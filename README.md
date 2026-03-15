Projeto Mercado - Versão Acadêmica Simples
```markdown
Sistema de Mercado — Protótipo (uso interno)

Resumo rápido:
- Interface desktop simples feita com Flet para uso por funcionários.
- Cadastro de fornecedores, produtos e entregadores.
- Controle de estoque por lotes com data de vencimento.
- Aplicação automática de desconto em produtos que estão próximos do vencimento (configurável por produto).
- Relatório diário exportável com produtos vencidos.
- Banco de dados em memória (não persistente) e dados de exemplo no início da aplicação.

Principais abstrações:
- Produtos são "canonicalizados" pelo nome (normalização) para evitar duplicatas quando fornecedores descrevem o mesmo item de formas diferentes.
- Cada fornecedor pode ter um preço próprio para um produto e uma descrição específica.
- Lotes (batches) armazenam quantidade, preço unitário e data de vencimento; o sistema calcula descontos automaticamente quando aplicável.

Como executar (Windows):

1. Criar e ativar um ambiente virtual (recomendado):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Instalar dependências:

```powershell
pip install -r requirements.txt
```

3. Executar a aplicação:

```powershell
python main.py
```

# Projeto Mercado — Protótipo Acadêmico

Pequeno protótipo de sistema de ponto de venda (POS) e controle de estoque, feito como exemplo acadêmico. A interface é desktop, construída com a biblioteca `flet` em Python.

Principais funcionalidades
- Tela Caixa: adicionar itens ao carrinho, aplicar descontos automáticos para lotes próximos do vencimento, finalizar venda e registrar entrega.
- Produtos: cadastro, edição e remoção de produtos (com configuração de desconto perto do vencimento).
- Fornecedores: cadastro de fornecedores e atribuição de preços por fornecedor para cada produto.
- Lotes/Estoque: cadastro de lotes com quantidade e data de vencimento; decremento FIFO simples ao finalizar vendas.
- Entregadores: gerenciamento de entregadores e registro de entregas pendentes.
- Relatórios: listas de lotes vencidos e próximos do vencimento.

Requisitos
- Python 3.9+ (testado em 3.9/3.10; versões mais recentes também devem funcionar).
- Dependências listadas em [requirements.txt](requirements.txt) (principal: `flet`).

Instalação (Windows — PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Execução

Preferível usar o comando do Flet para desenvolvimento:

```powershell
flet run main.py
```

Dependendo da versão do Flet, `python main.py` também pode funcionar.

Testes manuais rápidos (fluxos essenciais)
- Adicionar produto → Adicionar lote para o produto → Caixa: selecionar produto, quantidade, adicionar ao carrinho → Finalizar venda.
- Testar edição e remoção de produtos e lotes.
- Ativar "Entrega em casa" no Caixa, selecionar entregador e finalizar para registrar entrega pendente.

Notas de implementação e compatibilidade
- Banco em memória: o projeto usa `InMemoryDB` (dados não persistem ao encerrar a aplicação).
- DataPicker fallback: algumas versões do `flet` não aceitam `label` no `DatePicker`; o código trata esse caso e fornece um `TextField` fallback (`YYYY-MM-DD`).
- Overlay/Modal: há um overlay customizado para garantir compatibilidade entre versões do Flet; `show_message` usa prints de debug durante desenvolvimento.
- Funções de atualização de UI: procure por `reconstruir_*` (ex.: `reconstruir_lista_produtos`, `reconstruir_tabela_lotes`) — são responsáveis por sincronizar a visualização com o estado do DB.

Onde olhar no código
- Ponto de entrada: [main.py](main.py) — função `main(page)` monta toda a UI e handlers.
- Estruturas de dados e lógica de domínio: classe `InMemoryDB` em `main.py`.

Limitações conhecidas
- Sem persistência (arquivo ou banco) — dados voláteis.
- Validações de entrada e tratamento de erros são básicos; para produção, melhorar validação, mensagens de erro e testes automatizados.

Possíveis evoluções
- Persistência: SQLite/Postgres ou API backend.
- Autenticação/usuários e permissões.
- Testes automatizados (unitários e de interface).
- Internacionalização e melhorias de acessibilidade.
