import flet as ft
from utils import formatar_moeda


class ProdutosView:
    # --------------------- TELA: PRODUTOS ---------------------
    # A tela de produtos permite cadastrar novos produtos e ver a lista
    # com preços formatados. A função `rebuild_products_list` reconstrói
    # a `DataTable` usada para exibir os produtos.

    def __init__(self, page, db, overlay, product_dropdown, product_refresh_cb=None):
        self.page = page
        self.db = db
        self.overlay = overlay
        self.product_dropdown = product_dropdown
        # callback para notificar que produtos mudaram (ex: atualizar opções do caixa)
        self._product_refresh_cb = product_refresh_cb

        self.campo_nome_prod = ft.TextField(label='Nome', width=300)
        self.campo_codigo_prod = ft.TextField(label='Código (único)', width=200)
        self.campo_preco_prod = ft.TextField(label='Preço', value='0.0', width=150)
        self.campo_desconto_prod = ft.TextField(label='Desconto perto venc. (%)', value='0', width=150)
        self.campo_dias_perto = ft.TextField(label='Dias para considerar perto', value='7', width=150)
        self.btn_cadastrar_produto = ft.Button('Cadastrar produto')
        # id do produto sendo editado (None quando cadastro novo)
        self.id_produto_editando = None

        self.tabela_produtos = ft.DataTable(columns=[
            ft.DataColumn(ft.Text('ID')),
            ft.DataColumn(ft.Text('Nome')),
            ft.DataColumn(ft.Text('Código')),
            ft.DataColumn(ft.Text('Preço')),
            ft.DataColumn(ft.Text('Desconto (%)')),
            ft.DataColumn(ft.Text('Perto (dias)')),
            ft.DataColumn(ft.Text('Estoque')),
            ft.DataColumn(ft.Text('Ações')),
        ], rows=[])

        self.btn_cadastrar_produto.on_click = self.cadastrar_produto

        self.view = ft.Row([
            # coluna de cadastro com espaçamento maior entre campos
            ft.Column([ft.Text('Cadastrar produto'), self.campo_nome_prod, self.campo_codigo_prod, self.campo_preco_prod, self.campo_desconto_prod, self.campo_dias_perto, self.btn_cadastrar_produto], width=450, spacing=10),
            ft.VerticalDivider(width=20),
            ft.Column([ft.Text('Produtos cadastrados'), ft.Column([self.tabela_produtos], expand=True, scroll=ft.ScrollMode.AUTO)], expand=1)
        ], expand=True, alignment=ft.MainAxisAlignment.CENTER)
        # sanitizadores em tempo real para evitar letras em campos numéricos
        def sanitize_float_field(e, field):
            v = field.value or ''
            filtered = ''.join(ch for ch in v if (ch.isdigit() or ch == '.'))
            parts = filtered.split('.')
            if len(parts) > 1:
                filtered = parts[0] + '.' + ''.join(parts[1:])
            if filtered != v:
                field.value = filtered
                try:
                    field.update()
                except Exception:
                    pass

        def sanitize_int_field(e, field):
            v = field.value or ''
            filtered = ''.join(ch for ch in v if ch.isdigit())
            if filtered != v:
                field.value = filtered
                try:
                    field.update()
                except Exception:
                    pass

        self.campo_preco_prod.on_change = lambda e: sanitize_float_field(e, self.campo_preco_prod)
        self.campo_desconto_prod.on_change = lambda e: sanitize_float_field(e, self.campo_desconto_prod)
        self.campo_dias_perto.on_change = lambda e: sanitize_int_field(e, self.campo_dias_perto)

    def reconstruir_lista_produtos(self):
        # Reconstrói a tabela de produtos. Chamado após criar/editar/remover.
        self.tabela_produtos.rows.clear()
        estoque = self.db.estoque_disponivel()
        for p in self.db.produtos.values():
            self.tabela_produtos.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(str(p['id']))),
                ft.DataCell(ft.Text(p['nome'])),
                ft.DataCell(ft.Text(p['codigo'])),
                ft.DataCell(ft.Text(formatar_moeda(p['preco']))),
                ft.DataCell(ft.Text(str(p.get('desconto_perto_vencimento', 0)))),
                ft.DataCell(ft.Text(str(p.get('dias_perto', 7)))),
                ft.DataCell(ft.Text(str(estoque.get(p['id'], 0)))),
                ft.DataCell(ft.Row([
                    ft.IconButton(ft.icons.Icons.DELETE, tooltip='Remover', on_click=lambda e, pid=p['id']: self.remover_produto(pid)),
                    ft.IconButton(ft.icons.Icons.EDIT, tooltip='Editar', on_click=lambda e, pid=p['id']: self.iniciar_edicao_produto(pid))
                ]))
            ]))
        self.page.update()

    def reconstruir(self):
        self.reconstruir_lista_produtos()

    def selecionar_produto(self, name: str):
        # Função utilitária para selecionar um produto no dropdown do caixa
        # selecionar pelo nome para que o Dropdown mostre o texto legível
        # se for passado um id, convertemos para nome
        sel_name = name
        try:
            # se passarem id, encontrar o nome correspondente
            if isinstance(name, int) or str(name).isdigit():
                pid = int(name)
                p = self.db.produtos.get(pid)
                if p:
                    sel_name = p['nome']
        except Exception:
            pass
        self.product_dropdown.value = sel_name
        try:
            self.product_dropdown.update()
        except Exception:
            pass

    def remover_produto(self, pid):
        # remover_produto (UI handler): chama o DB para remover o produto
        # e atualiza dropdowns/tabelas; também cancela qualquer edição
        # em andamento se o produto removido estiver sendo editado.
        try:
            self.db.remover_produto(pid)
        except Exception as ex:
            self.overlay.mostrar_mensagem('Erro', str(ex))
            return
        # atualizar lista e dropdowns
        self.reconstruir_lista_produtos()
        if self._product_refresh_cb:
            try:
                self._product_refresh_cb()
            except Exception:
                pass
        # atualização do dropdown do caixa é gerenciada pela tela de Caixa
        if self.id_produto_editando == pid:
            # cancelar edição se estava editando este produto
            self.id_produto_editando = None
            self.btn_cadastrar_produto.text = 'Cadastrar produto'
            try:
                self.btn_cadastrar_produto.update()
            except Exception:
                pass

    def iniciar_edicao_produto(self, pid):
        # iniciar_edicao_produto: pré-preenche o formulário de cadastro com
        # os dados do produto selecionado para edição e troca o texto
        # do botão para 'Salvar alterações'.
        p = self.db.produtos.get(pid)
        if not p:
            self.overlay.mostrar_mensagem('Erro', 'Produto não encontrado')
            return
        self.id_produto_editando = pid
        self.campo_nome_prod.value = p['nome']
        self.campo_codigo_prod.value = p['codigo']
        self.campo_preco_prod.value = str(p['preco'])
        self.campo_desconto_prod.value = str(p.get('desconto_perto_vencimento', 0))
        self.campo_dias_perto.value = str(p.get('dias_perto', 7))
        # mostrar estoque atual no formulário (somente leitura)
        try:
            estoque = self.db.estoque_disponivel().get(p['id'], 0)
            if not hasattr(self, 'campo_estoque'):
                self.campo_estoque = ft.Text(f'Estoque: {estoque}')
                # inserir antes do botão
                self.view.controls[0].controls.insert(-1, self.campo_estoque)
            else:
                self.campo_estoque.value = f'Estoque: {estoque}'
                try:
                    self.campo_estoque.update()
                except Exception:
                    pass
        except Exception:
            pass
        self.btn_cadastrar_produto.text = 'Salvar alterações'
        try:
            # garantir que os campos sejam atualizados na UI imediatamente
            self.campo_nome_prod.update()
            self.campo_codigo_prod.update()
            self.campo_preco_prod.update()
            self.campo_desconto_prod.update()
            self.campo_dias_perto.update()
            self.btn_cadastrar_produto.update()
            self.page.update()
        except Exception:
            pass

    def cadastrar_produto(self, e):
        # cadastrar_produto: handler do botão de cadastrar/salvar produto.
        # Se `id_produto_editando` for None, cria um novo produto.
        # Caso contrário, atualiza o produto em edição.
        try:
            name = self.campo_nome_prod.value.strip()
            code = self.campo_codigo_prod.value.strip()
            price = float(self.campo_preco_prod.value)
            discount = float(self.campo_desconto_prod.value)
            near_days = int(self.campo_dias_perto.value)
            if self.id_produto_editando is None:
                self.db.adicionar_produto(name, code, price, discount, near_days)
            else:
                self.db.atualizar_produto(self.id_produto_editando, name, code, price, discount, near_days)
                self.id_produto_editando = None
                self.btn_cadastrar_produto.text = 'Cadastrar produto'
                try:
                    self.btn_cadastrar_produto.update()
                except Exception:
                    pass
            self.campo_nome_prod.value = ''
            self.campo_codigo_prod.value = ''
            self.campo_preco_prod.value = '0.0'
            self.campo_desconto_prod.value = '0'
            self.campo_dias_perto.value = '7'
            self.reconstruir_lista_produtos()
            # notificar a tela de caixa para atualizar dropdowns
            if self._product_refresh_cb:
                try:
                    self._product_refresh_cb()
                except Exception:
                    pass
            self.page.update()
        except Exception as ex:
            self.overlay.mostrar_mensagem('Erro ao cadastrar', str(ex))
