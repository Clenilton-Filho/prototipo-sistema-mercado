import flet as ft
from utils import formatar_moeda


class FornecedoresView:
    # --------------------- TELA: FORNECEDORES ---------------------
    # lado a lado: lista de fornecedores e formulário de adicionar

    def __init__(self, page, db, overlay):
        self.page = page
        self.db = db
        self.overlay = overlay
        # id do fornecedor atualmente selecionado na tela de fornecedores
        self.selected_supplier_id = None

        self.lista_fornecedores = ft.ListView(width=300, spacing=5)
        self.campo_nome_fornecedor = ft.TextField(label='Nome fornecedor', width=300)
        self.btn_adicionar_fornecedor = ft.Button('Adicionar fornecedor')

        # Formulário para atribuir produtos a um fornecedor (na área de "Adicionar fornecedor")
        self.dropdown_fornecedor_atribuir = ft.Dropdown(label='Fornecedor (atribuir)', width=300, options=[ft.dropdown.Option(s['nome']) for s in db.fornecedores.values()])
        self.dropdown_produto_fornecedor_novo = ft.Dropdown(label='Produto', width=250, options=[ft.dropdown.Option(p['nome']) for p in db.produtos.values()])
        self.campo_preco_fornecedor_novo = ft.TextField(label='Preço do fornecedor', value='0.0', width=150)
        self.btn_atribuir_ao_fornecedor = ft.Button('Atribuir produto ao fornecedor')

        # Formulário que aparece dentro da área de detalhes do fornecedor selecionado
        self.dropdown_produto_fornecedor_selecionado = ft.Dropdown(label='Produto', width=250, options=[ft.dropdown.Option(p['nome']) for p in db.produtos.values()])
        self.campo_preco_fornecedor_selecionado = ft.TextField(label='Preço do fornecedor', value='0.0', width=150)
        self.btn_atribuir_selecionado = ft.Button('Atribuir a este fornecedor')

        self.detalhes_fornecedor = ft.Column()  # mostrará o que o fornecedor vende e o formulário de atribuição
        self.tabela_produtos_fornecedor = ft.DataTable(columns=[
            ft.DataColumn(ft.Text('Produto')),
            ft.DataColumn(ft.Text('Preço')),
        ], rows=[])

        self.btn_adicionar_fornecedor.on_click = self.adicionar_fornecedor
        self.btn_atribuir_ao_fornecedor.on_click = self.atribuir_para_fornecedor_do_meio
        self.btn_atribuir_selecionado.on_click = self.atribuir_para_fornecedor_selecionado

        self.view = ft.Row([
            # esquerda: formulário de cadastro/atribuição (antes estava no meio)
            ft.Column([ft.Text('Adicionar fornecedor'), self.campo_nome_fornecedor, self.btn_adicionar_fornecedor, ft.Divider(), ft.Text('Atribuir produto a fornecedor (selecionar fornecedor)'), self.dropdown_fornecedor_atribuir, self.dropdown_produto_fornecedor_novo, self.campo_preco_fornecedor_novo, self.btn_atribuir_ao_fornecedor], width=420),
            ft.VerticalDivider(width=20),
            # centro: lista de fornecedores (label atualizado)
            ft.Column([ft.Text('Fornecedores - clique para mais detalhes'), self.lista_fornecedores], width=320),
            ft.VerticalDivider(width=20),
            # direita: detalhes do fornecedor
            ft.Column([ft.Text('Detalhes do fornecedor'), self.detalhes_fornecedor], expand=1)
        ], expand=True)

    def reconstruir_lista_fornecedores(self):
        self.lista_fornecedores.controls.clear()
        for s in self.db.fornecedores.values():
            self.lista_fornecedores.controls.append(ft.Row([
                ft.Text(s['nome'], expand=1),
                ft.TextButton('Ver', on_click=lambda e, sid=s['id']: self.selecionar_fornecedor(sid))
            ]))
        # atualizar dropdowns de seleção
        self.dropdown_fornecedor_atribuir.options = [ft.dropdown.Option(s['nome']) for s in self.db.fornecedores.values()]
        self.dropdown_produto_fornecedor_novo.options = [ft.dropdown.Option(p['nome']) for p in self.db.produtos.values()]
        self.dropdown_produto_fornecedor_selecionado.options = [ft.dropdown.Option(p['nome']) for p in self.db.produtos.values()]
        self.page.update()

    def reconstruir(self):
        self.reconstruir_lista_fornecedores()

    def selecionar_fornecedor(self, sid):
        self.selected_supplier_id = sid
        s = self.db.fornecedores[sid]
        self.detalhes_fornecedor.controls.clear()
        self.detalhes_fornecedor.controls.append(ft.Text(f"Fornecedor: {s['nome']}"))
        self.detalhes_fornecedor.controls.append(ft.Divider())
        self.detalhes_fornecedor.controls.append(ft.Text('Atribuir produto a este fornecedor'))
        self.detalhes_fornecedor.controls.append(self.dropdown_produto_fornecedor_selecionado)
        self.detalhes_fornecedor.controls.append(self.campo_preco_fornecedor_selecionado)
        self.detalhes_fornecedor.controls.append(self.btn_atribuir_selecionado)
        self.detalhes_fornecedor.controls.append(ft.Divider())
        self.tabela_produtos_fornecedor.rows.clear()
        for pid, price in s['produtos'].items():
            p = self.db.produtos.get(pid)
            self.tabela_produtos_fornecedor.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(p['nome'] if p else '')),
                ft.DataCell(ft.Text(formatar_moeda(price)))
            ]))
        self.detalhes_fornecedor.controls.append(self.tabela_produtos_fornecedor)
        self.page.update()

    def atribuir_para_fornecedor_do_meio(self, e):
        sup_name = self.dropdown_fornecedor_atribuir.value
        prod_name_local = self.dropdown_produto_fornecedor_novo.value
        if not sup_name or not prod_name_local:
            self.overlay.mostrar_mensagem('Erro', 'Selecione fornecedor e produto')
            return
        sid = next((i for i, sv in self.db.fornecedores.items() if sv['nome'] == sup_name), None)
        prod = next((p for p in self.db.produtos.values() if p['nome'] == prod_name_local), None)
        if sid is None or prod is None:
            self.overlay.mostrar_mensagem('Erro', 'Fornecedor ou produto inválido')
            return
        try:
            self.db.fornecedor_definir_preco(sid, prod['id'], float(self.campo_preco_fornecedor_novo.value))
            self.reconstruir_lista_fornecedores()
            if self.selected_supplier_id == sid:
                self.selecionar_fornecedor(sid)
        except Exception as ex:
            self.overlay.mostrar_mensagem('Erro', str(ex))

    def atribuir_para_fornecedor_selecionado(self, e):
        if self.selected_supplier_id is None:
            self.overlay.mostrar_mensagem('Erro', 'Selecione um fornecedor (Ver)')
            return
        prod_name_local = self.dropdown_produto_fornecedor_selecionado.value
        if not prod_name_local:
            self.overlay.mostrar_mensagem('Erro', 'Selecione um produto')
            return
        prod = next((p for p in self.db.produtos.values() if p['nome'] == prod_name_local), None)
        try:
            self.db.fornecedor_definir_preco(self.selected_supplier_id, prod['id'], float(self.campo_preco_fornecedor_selecionado.value))
            self.selecionar_fornecedor(self.selected_supplier_id)
            self.reconstruir_lista_fornecedores()
        except Exception as ex:
            self.overlay.mostrar_mensagem('Erro', str(ex))

    def adicionar_fornecedor(self, e):
        try:
            sid = self.db.adicionar_fornecedor(self.campo_nome_fornecedor.value.strip())
            # se preencher produto no formulário de criação, já atribui
            if self.dropdown_produto_fornecedor_novo.value:
                prod = next((p for p in self.db.produtos.values() if p['nome'] == self.dropdown_produto_fornecedor_novo.value), None)
                if prod:
                    try:
                        self.db.fornecedor_definir_preco(sid, prod['id'], float(self.campo_preco_fornecedor_novo.value))
                    except Exception:
                        pass
            self.campo_nome_fornecedor.value = ''
            self.dropdown_produto_fornecedor_novo.value = None
            self.campo_preco_fornecedor_novo.value = '0.0'
            self.reconstruir_lista_fornecedores()
            # selecionar o novo fornecedor no dropdown de atribuição
            if self.db.fornecedores:
                last_sid = max(self.db.fornecedores.keys())
                self.dropdown_fornecedor_atribuir.value = self.db.fornecedores[last_sid]['nome']
                self.dropdown_fornecedor_atribuir.update()
            self.page.update()
        except Exception as ex:
            self.overlay.mostrar_mensagem('Erro ao cadastrar fornecedor', str(ex))
