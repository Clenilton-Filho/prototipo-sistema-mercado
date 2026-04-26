import flet as ft
from datetime import datetime, timedelta


class LotesView:
    # --------------------- TELA: ADD LOTE (ESTOQUE) ---------------------

    def __init__(self, page, db, overlay):
        self.page = page
        self.db = db
        self.overlay = overlay
        # id do lote sendo editado
        self.editing_batch_id = None

        self.lote_product_dropdown = ft.Dropdown(options=[ft.dropdown.Option(p['nome']) for p in db.produtos.values()], hint_text='Selecione o produto')
        self.lote_supplier_dropdown = ft.Dropdown(options=[ft.dropdown.Option(s['nome']) for s in db.fornecedores.values()], hint_text='Fornecedor (opcional)')
        self.lote_qty = ft.TextField(value='1', width=150, hint_text='Quantidade (ex: 10)')
        # Criar DatePicker com fallback:
        # Algumas versões do Flet aceitam `label` no construtor de
        # `DatePicker`, outras não. Para garantir que o formulário funcione
        # em ambientes diferentes (desktop/web/versões antigas), fazemos:
        # 1) Tentar criar `DatePicker(label=...)` — se funcionar, usamos.
        # 2) Se gerar erro, criamos um `Text` como label e um `TextField`
        #    de fallback para que o usuário possa digitar a data no
        #    formato `YYYY-MM-DD`.
        try:
            self.lote_expiry = ft.DatePicker(label='Data de vencimento', width=220, value=(datetime.today() + timedelta(days=30)).date())
            self.lote_expiry_label = None
            self.lote_expiry_field = None
        except Exception:
            # fallback: DatePicker sem label pode existir, mas para ser mais
            # explícitos usamos `lote_expiry=None` e um `TextField` como
            # entrada de data alternativa.
            self.lote_expiry = None
            self.lote_expiry_label = ft.Text('Data de vencimento')
            self.lote_expiry_field = ft.TextField(hint_text='YYYY-MM-DD', width=220)
        self.add_lote_btn = ft.Button('Adicionar lote')

        self.lote_table = ft.DataTable(columns=[
            ft.DataColumn(ft.Text('ID')),
            ft.DataColumn(ft.Text('Produto')),
            ft.DataColumn(ft.Text('Fornecedor')),
            ft.DataColumn(ft.Text('Quantidade')),
            ft.DataColumn(ft.Text('Vencimento')),
            ft.DataColumn(ft.Text('Ações')),
        ], rows=[])

        self.add_lote_btn.on_click = self.add_lote

        # montar dinamicamente os controles do formulário (incluir label separado quando necessário)
        lote_form_controls = [ft.Text('Adicionar lote'), self.lote_product_dropdown, self.lote_supplier_dropdown, self.lote_qty]
        if self.lote_expiry_label is not None:
            lote_form_controls.append(self.lote_expiry_label)
        # anexar o controle disponível: DatePicker ou TextField fallback
        if self.lote_expiry is not None:
            lote_form_controls.append(self.lote_expiry)
        elif self.lote_expiry_field is not None:
            lote_form_controls.append(self.lote_expiry_field)
        lote_form_controls.append(self.add_lote_btn)

        self.view = ft.Row([
            ft.Column(lote_form_controls, width=420, spacing=10),
            ft.VerticalDivider(width=20),
            ft.Column([ft.Text('Lotes/Estoque atual'), self.lote_table], expand=1)
        ], expand=True)

    def reconstruir_tabela_lotes(self):
        self.lote_table.rows.clear()
        for b in self.db.lotes:
            p = self.db.produtos.get(b.get('produto_id'))
            s = self.db.fornecedores.get(b.get('fornecedor_id')) if b.get('fornecedor_id') else None
            fornecedor_nome = s['nome'] if s else '-'
            self.lote_table.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(str(b['id']))),
                ft.DataCell(ft.Text(p['nome'] if p else '')),
                ft.DataCell(ft.Text(fornecedor_nome)),
                ft.DataCell(ft.Text(str(b.get('quantidade')))),
                ft.DataCell(ft.Text(b.get('vencimento_raw') or '')),
                ft.DataCell(ft.Row([
                    ft.IconButton(ft.icons.Icons.DELETE, tooltip='Remover', on_click=lambda e, bid=b['id']: self.remover_lote_ui(bid)),
                    ft.IconButton(ft.icons.Icons.EDIT, tooltip='Editar', on_click=lambda e, bid=b['id']: self.iniciar_edicao_lote(bid))
                ]))
            ]))
        self.page.update()

    def reconstruir(self):
        self.reconstruir_tabela_lotes()

    def add_lote(self, e):
        # add_lote: handler do botão de adicionar/editar lote.
        # Aceita tanto o `DatePicker` (quando disponível) quanto o
        # `TextField` fallback. Constrói a string `expiry_raw` e cria
        # ou atualiza o lote no banco.
        if not self.lote_product_dropdown.value:
            self.overlay.mostrar_mensagem('Erro', 'Selecione o produto')
            return
        prod = next((p for p in self.db.produtos.values() if p['nome'] == self.lote_product_dropdown.value), None)
        sup = next((s for s in self.db.fornecedores.values() if s['nome'] == self.lote_supplier_dropdown.value), None) if self.lote_supplier_dropdown.value else None
        try:
            # aceita DatePicker (objeto date) ou string. Se DatePicker não suportado, usa campo de texto YYYY-MM-DD
            if self.lote_expiry is not None:
                expiry_val = self.lote_expiry.value
            else:
                expiry_val = self.lote_expiry_field.value
            if hasattr(expiry_val, 'strftime'):
                expiry_raw = expiry_val.strftime('%Y-%m-%d')
            else:
                expiry_raw = str(expiry_val)
            if self.editing_batch_id is None:
                self.db.adicionar_lote(prod['id'], sup['id'] if sup else None, int(self.lote_qty.value), expiry_raw)
            else:
                self.db.atualizar_lote(self.editing_batch_id, prod['id'], sup['id'] if sup else None, int(self.lote_qty.value), expiry_raw)
                self.editing_batch_id = None
                self.add_lote_btn.text = 'Adicionar lote'
                try:
                    self.add_lote_btn.update()
                except Exception:
                    pass
            self.reconstruir_tabela_lotes()
        except Exception as ex:
            self.overlay.mostrar_mensagem('Erro', str(ex))

    def remover_lote_ui(self, bid):
        self.db.remover_lote(bid)
        self.reconstruir_tabela_lotes()

    def iniciar_edicao_lote(self, bid):
        # start_edit_batch: pré-preenche o formulário de lote com os
        # valores do lote selecionado para edição (produto, fornecedor,
        # quantidade e data). Ajusta o botão para salvar alterações.
        b = next((x for x in self.db.lotes if x['id'] == bid), None)
        if not b:
            self.overlay.mostrar_mensagem('Erro', 'Lote não encontrado')
            return
        self.editing_batch_id = bid
        # preencher campos
        prod = self.db.produtos.get(b.get('produto_id'))
        self.lote_product_dropdown.value = prod['nome'] if prod else None
        self.lote_supplier_dropdown.value = self.db.fornecedores[b.get('fornecedor_id')]['nome'] if b.get('fornecedor_id') and b.get('fornecedor_id') in self.db.fornecedores else None
        self.lote_qty.value = str(b.get('quantidade'))
        try:
            if self.lote_expiry is not None:
                self.lote_expiry.value = b.get('vencimento') if b.get('vencimento') else None
            elif self.lote_expiry_field is not None:
                self.lote_expiry_field.value = b.get('vencimento_raw') if b.get('vencimento_raw') else ''
        except Exception:
            pass
        self.add_lote_btn.text = 'Salvar alterações'
        try:
            self.add_lote_btn.update()
        except Exception:
            pass
