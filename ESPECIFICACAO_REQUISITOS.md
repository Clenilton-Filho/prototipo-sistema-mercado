# Especificação de Requisitos — Protótipo Sistema Mercado

**1. Visão Geral**

Sistema de mercado com múltiplas telas, contemplando autenticação de usuários com hash seguro,
CRUD de produtos, fornecedores e lotes, fluxo de vendas no Caixa com desconto automático
para lotes próximos ao vencimento, relatórios de vencidos e gestão de entregadores.

Escopo: operações locais (offline) voltadas para uso interno por funcionários.

---

**2. Atores**

- Funcionário (usuário comum): opera o caixa, consulta produtos e vendas.
- Administrador / Gestor: cadastra/edita produtos, fornecedores, lotes e configurações.
- Entregador: registra entregas (CRUD gerenciado pelo Administrador).
- Sistema (comportamento automático): aplica descontos próximos ao vencimento, calcula estoque.

---

**3. Telas relevantes**

- Tela de Autenticação: [views/auth.py](views/auth.py)
- Tela Principal / Navegação: [views/app.py](views/app.py), [views/overlay.py](views/overlay.py)
- Tela Produtos: [views/produtos.py](views/produtos.py)
- Tela Fornecedores: [views/fornecedores.py](views/fornecedores.py)
- Tela Lotes: [views/lotes.py](views/lotes.py)
- Tela Caixa (vendas): [views/caixa.py](views/caixa.py)
- Tela Relatórios: [views/relatorios.py](views/relatorios.py)
- Tela Entregadores: [views/entregadores.py](views/entregadores.py)
- Persistência e regras de negócio: [banco_SQLITE.py](banco_SQLITE.py)

---

**4. Requisitos Funcionais**

- RF001 — Permitir autenticação de funcionários
  - Atores: Funcionário
  - Prioridade: Must have
  - Telas/Módulos: [views/auth.py](views/auth.py), [banco_SQLITE.py](banco_SQLITE.py)
  - Critério de aceitação: usuário com credenciais válidas acessa a aplicação; credenciais inválidas produzem mensagem de erro.
    - O que foi implementado: Tela de login em [views/auth.py](views/auth.py); armazenamento e verificação
      de senhas com PBKDF2-HMAC-SHA256 em [banco_SQLITE.py](banco_SQLITE.py) (`adicionar_usuario`, `autenticar_usuario`).

- RF002 — Cadastrar, editar e listar produtos
  - Atores: Administrador
  - Prioridade: Must have
  - Telas/Módulos: [views/produtos.py](views/produtos.py), [banco_SQLITE.py](banco_SQLITE.py)
  - Critério de aceitação: produto com nome e preço salvo e visível na listagem; validação de campos (preço >= 0).
    - O que foi implementado: Tela de Produtos em [views/produtos.py](views/produtos.py) com formulários de
      criação/edição; métodos de persistência em [banco_SQLITE.py](banco_SQLITE.py) para CRUD de produtos.

- RF003 — Cadastrar, editar e listar fornecedores permitindo nomes iguais com descrições distintas
  - Atores: Administrador
  - Prioridade: Should have
  - Telas/Módulos: [views/fornecedores.py](views/fornecedores.py), [banco_SQLITE.py](banco_SQLITE.py)
  - Critério de aceitação: dois fornecedores com mesmo `nome` e descrições diferentes podem ser salvos.
    - O que foi implementado: Ajuste no esquema e lógica de persistência (`suppliers` com `UNIQUE(nome, descricao)`) em
      [banco_SQLITE.py](banco_SQLITE.py); views atualizadas ([views/fornecedores.py](views/fornecedores.py),
      [views/lotes.py](views/lotes.py)) exibindo `"nome — descricao"` nos dropdowns, e funções de busca que
      desambiguam por `nome`+`descricao` (fallback por `nome` ou `id`).

- RF004 — Cadastrar, editar e listar lotes vinculados a produtos e fornecedores
  - Atores: Administrador
  - Prioridade: Must have
  - Telas/Módulos: [views/lotes.py](views/lotes.py), [banco_SQLITE.py](banco_SQLITE.py)
  - Critério de aceitação: lote inclui `produto`, `fornecedor`, `quantidade`, `data_vencimento`.
    - O que foi implementado: Tela Lotes em [views/lotes.py](views/lotes.py) com associação a produto e fornecedor;
      funções de persistência em [banco_SQLITE.py](banco_SQLITE.py) (`adicionar_lote`, `atualizar_lote`, `remover_lote`).

- RF005 — Registrar vendas no Caixa e decrementar estoque por vencimento
  - Atores: Funcionário
  - Prioridade: Must have
  - Telas/Módulos: [views/caixa.py](views/caixa.py), [banco_SQLITE.py](banco_SQLITE.py)
  - Critério de aceitação: ao finalizar venda, estoque disponível é reduzido considerando lotes não vencidos; lotes com menor data de vencimento são usados primeiro.
    - O que foi implementado: Tela Caixa em [views/caixa.py](views/caixa.py) com fluxo de venda;
      lógica de estoque em [banco_SQLITE.py](banco_SQLITE.py) que calcula `estoque_disponivel()` e aplica retirada
      de lotes seguindo ordem por data de vencimento.

- RF006 — Aplicar desconto automático a produtos com lotes próximos do vencimento
  - Atores: Sistema (automático), Funcionário
  - Prioridade: Should have
  - Telas/Módulos: [views/caixa.py](views/caixa.py), [banco_SQLITE.py](banco_SQLITE.py) (campos `desconto_perto_vencimento`, `dias_perto`)
  - Critério de aceitação: ao adicionar item ao carrinho, se existir lote dentro de `dias_perto`, aplicar desconto configurado ao preço exibido.
    - O que foi implementado: Campos em produtos (`desconto_perto_vencimento`, `dias_perto`) e função
      `produtos_perto_vencimento()` em [banco_SQLITE.py](banco_SQLITE.py); integração em [views/caixa.py](views/caixa.py)
      que mostra o desconto e ajusta o total automaticamente.

- RF007 — Gerar relatórios de lotes vencidos e próximos do vencimento
  - Atores: Administrador
  - Prioridade: Could have
  - Telas/Módulos: [views/relatorios.py](views/relatorios.py), [banco_SQLITE.py](banco_SQLITE.py)
  - Critério de aceitação: relatório lista lotes vencidos e próximos com quantidade e produto.
    - O que foi implementado: Tela Relatórios em [views/relatorios.py](views/relatorios.py) que consome
      `produtos_vencidos()` e `produtos_perto_vencimento()` de [banco_SQLITE.py](banco_SQLITE.py) para exibir listas.

- RF008 — Gerenciar entregadores e registrar entregas associadas a vendas
  - Atores: Administrador, Entregador
  - Prioridade: Could have
  - Telas/Módulos: [views/entregadores.py](views/entregadores.py), [views/caixa.py](views/caixa.py), [banco_SQLITE.py](banco_SQLITE.py)
  - Critério de aceitação: entregador cadastrado aparece na lista e pode ser associado a entrega ao finalizar venda.
    - O que foi implementado: CRUD de entregadores em [views/entregadores.py](views/entregadores.py) e
      registro de entregas integrado ao fluxo de finalização de venda em [views/caixa.py](views/caixa.py) com persistência em `banco_SQLITE.py`.

---

**5. Requisitos Não Funcionais**

- RNF001 — Armazenamento seguro de senhas
  - Categoria: Segurança
  - Métrica: Senhas persistidas usando criptografia PBKDF2-HMAC-SHA256 com salt.
  - O que foi implementado: Implementação real de hashing e verificação em [banco_SQLITE.py](banco_SQLITE.py) (PBKDF2),
    com salt por usuário; não há armazenamento de senhas em texto simples.

- RNF002 — Desempenho da UI
  - Categoria: Desempenho
  - Métrica: Listagens (produtos/lotes) devem carregar em < 1s com dataset local de até 1000 itens.
  - O que foi implementado: As views são implementadas em Flet e usam renderização incremental simples, permitindo navegação fluida.

- RNF003 — Usabilidade mínima do caixa
  - Categoria: Usabilidade
  - Métrica: completar uma venda comum em ≤ 3 telas e ≤ 6 cliques a partir da tela principal.
  - O que foi implementado: Fluxo de venda centralizado em [views/caixa.py](views/caixa.py) com adição rápida de itens,
    aplicação automática de descontos e finalização em uma única sequência de interações; telas modais e overlays
    em [views/overlay.py](views/overlay.py) reduzem cliques desnecessários.

- RNF004 — Consistência e integridade do banco de dados
  - Categoria: Confiabilidade
  - Métrica: operações de escrita (adicionar/atualizar lote, venda) devem ser atômicas; o DB não deve ficar em estado inconsistente após encerramento inesperado.
  - O que foi implementado: Uso de transações SQLite nas operações críticas dentro de [banco_SQLITE.py](banco_SQLITE.py); tabelas e constraints
    (incluindo `UNIQUE(nome, descricao)` em `suppliers`) ajudam a manter integridade. 
- RNF005 — Portabilidade e execução local
  - Categoria: Operacional
  - Métrica: executar em Windows com Python 3.9+ e dependências em `requirements.txt`.
  - O que foi implementado: Projeto inclui `requirements.txt` e portável pela implementação em python. A arquitetura é local
    (arquivo `data/mercado.db`) e não requer servidor web.

---

**6. Casos de Uso **

- Login
  - Ator: Funcionário
  - Fluxo principal: abrir app → inserir credenciais → autenticar → acessar tela principal.

- Gerenciar Fornecedores
  - Ator: Administrador
  - Fluxo principal: abrir Tela Fornecedores → criar/editar/visualizar fornecedor → salvar → ver na lista.

- Registrar Lote
  - Ator: Administrador
  - Fluxo principal: abrir Tela Lotes → selecionar produto → selecionar fornecedor (label `nome — descricao`) → informar quantidade e vencimento → salvar.

- Realizar Venda
  - Ator: Funcionário
  - Fluxo principal: abrir Caixa → adicionar produtos ao carrinho → aplicar desconto automático se aplicável → finalizar venda → registrar entrega (opcional).