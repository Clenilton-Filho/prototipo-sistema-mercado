import flet as ft
from datetime import datetime, timedelta


class LotesView:
    # --------------------- TELA: ADD LOTE (ESTOQUE) ---------------------

    def __init__(self, page, db, overlay, product_refresh_cb=None):
        self.page = page
        self.db = db
        self.overlay = overlay
        self._product_refresh_cb = product_refresh_cb
        # id do lote sendo editado
        self.editing_batch_id = None
        # opções iniciais para dropdowns de produto/fornecedor (apenas nomes)
        prod_opts = [ft.dropdown.Option(p['nome']) for p in db.produtos.values()]
        def _sup_label(s):
            return f"{s['nome']} — {s.get('descricao','')}" if s.get('descricao') else f"{s['nome']}"
        sup_opts = [ft.dropdown.Option(_sup_label(s)) for s in db.fornecedores.values()]
        self.lote_product_dropdown = ft.Dropdown(options=prod_opts, hint_text='Selecione o produto')
        self.lote_supplier_dropdown = ft.Dropdown(options=sup_opts, hint_text='Fornecedor (opcional)')
        self.lote_qty = ft.TextField(value='1', width=150, hint_text='Quantidade (ex: 10)')
        # Date inputs implementados como campos numéricos (DD/MM/AAAA)
        self.lote_expiry_label = ft.Text('Data de vencimento (DD/MM/AAAA)')
        self.lote_day = ft.TextField(value='', width=80, hint_text='DD')
        self.lote_month = ft.TextField(value='', width=80, hint_text='MM')
        current_year = datetime.today().year
        self.lote_year = ft.TextField(value=str(current_year), width=120, hint_text='AAAA')
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

        # montar controles do formulário (date-picker por dia/mês/ano)
        date_row = ft.Row([self.lote_day, self.lote_month, self.lote_year], spacing=10)
        lote_form_controls = [ft.Text('Adicionar lote'), self.lote_product_dropdown, self.lote_supplier_dropdown, self.lote_qty, self.lote_expiry_label, date_row]
        lote_form_controls.append(self.add_lote_btn)

        # sanitizadores para evitar letras em campos numéricos e data
        def sanitize_int_field(e, field):
            v = field.value or ''
            filtered = ''.join(ch for ch in v if ch.isdigit())
            if filtered != v:
                field.value = filtered
                try:
                    field.update()
                except Exception:
                    pass

        self.lote_qty.on_change = lambda e: sanitize_int_field(e, self.lote_qty)
        # aplicar sanitização aos campos de data
        self.lote_day.on_change = lambda e: sanitize_int_field(e, self.lote_day)
        self.lote_month.on_change = lambda e: sanitize_int_field(e, self.lote_month)
        self.lote_year.on_change = lambda e: sanitize_int_field(e, self.lote_year)

        self.view = ft.Row([
            ft.Column(lote_form_controls, width=420, spacing=10),
            ft.VerticalDivider(width=20),
            ft.Column([ft.Text('Lotes/Estoque atual'), ft.Column([self.lote_table], expand=True, scroll=ft.ScrollMode.AUTO)], expand=1)
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
        # atualizar opções dos dropdowns antes de reconstruir a tabela
        try:
            prod_opts = [ft.dropdown.Option(p['nome']) for p in self.db.produtos.values()]
            self.lote_product_dropdown.options = prod_opts
            self.lote_product_dropdown.update()
        except Exception:
            pass
        try:
            def _sup_label(s):
                return f"{s['nome']} — {s.get('descricao','')}" if s.get('descricao') else f"{s['nome']}"
            sup_opts = [ft.dropdown.Option(_sup_label(s)) for s in self.db.fornecedores.values()]
            self.lote_supplier_dropdown.options = sup_opts
            self.lote_supplier_dropdown.update()
        except Exception:
            pass
        self.reconstruir_tabela_lotes()

    def add_lote(self, e):
        # add_lote: handler do botão de adicionar/editar lote.
        # Constrói a string `expiry_raw` a partir dos campos numéricos
        # de data (DD/MM/AAAA) e cria ou atualiza o lote no banco.
        # Observações de validação/importância:
        # - Os campos de data são validados como números (DD/MM/AAAA).
        # - A função notifica a view `Caixa` via callback para atualizar
        #   opções/estoque exibido quando lotes mudam.
        # extrair seleção de produto/fornecedor de forma robusta
        def _sel_text(s):
            if s is None:
                return ''
            if isinstance(s, str):
                return s.strip()
            for attr in ('value', 'text', 'label', 'key'):
                v = getattr(s, attr, None)
                if v is not None:
                    return str(v).strip()
            return str(s).strip()

        prod_sel = _sel_text(self.lote_product_dropdown.value)
        if not prod_sel:
            self.overlay.mostrar_mensagem('Erro', 'Selecione o produto')
            return
        # tentar interpretar como id
        prod = None
        # primeira tentativa: buscar por nome (nossas Options expõem nomes)
        prod = next((p for p in self.db.produtos.values() if (p['nome'] or '').strip() == prod_sel), None)
        if prod is None:
            # fallback: interpretar como id
            try:
                pid = int(prod_sel)
                prod = self.db.produtos.get(pid)
            except Exception:
                pass
        sup = None
        if self.lote_supplier_dropdown.value:
            sup_sel = _sel_text(self.lote_supplier_dropdown.value)
            # sup_sel may be 'Nome — Descrição'
            parts = sup_sel.split(' — ', 1)
            sup_nome = parts[0].strip()
            sup_desc = parts[1].strip() if len(parts) > 1 else ''
            sup = next((s for s in self.db.fornecedores.values() if (s.get('nome') or '').strip() == sup_nome and (s.get('descricao') or '').strip() == sup_desc), None)
            if sup is None:
                # fallback: try name-only match
                sup = next((s for s in self.db.fornecedores.values() if (s.get('nome') or '').strip() == sup_nome), None)
            if sup is None:
                try:
                    sid = int(sup_sel)
                    sup = self.db.fornecedores.get(sid)
                except Exception:
                    pass
        if not prod:
            self.overlay.mostrar_mensagem('Erro', 'Produto inválido')
            return
        # validar quantidade
        try:
            qty = int(self.lote_qty.value)
            if qty <= 0:
                raise ValueError()
        except Exception:
            self.overlay.mostrar_mensagem('Erro', 'Quantidade inválida')
            return
        # Montar `expiry_raw` a partir dos campos numéricos (dia, mês, ano)
        try:
            # montar expiry_raw a partir dos campos numéricos (dia, mês, ano)
            day = (self.lote_day.value or '').strip()
            month = (self.lote_month.value or '').strip()
            year = (self.lote_year.value or '').strip()
            if day and month and year:
                try:
                    dd = int(day)
                    mm = int(month)
                    yyyy = int(year)
                    expiry_raw = f"{yyyy:04d}-{mm:02d}-{dd:02d}"
                    # validar data
                    datetime.strptime(expiry_raw, '%Y-%m-%d')
                except Exception:
                    self.overlay.mostrar_mensagem('Erro', 'Data de vencimento inválida')
                    return
            else:
                expiry_raw = None
        except Exception as ex:
            self.overlay.mostrar_mensagem('Erro', str(ex))
            return
        try:
            if self.editing_batch_id is None:
                self.db.adicionar_lote(prod['id'], sup['id'] if sup else None, int(qty), expiry_raw)
            else:
                self.db.atualizar_lote(self.editing_batch_id, prod['id'], sup['id'] if sup else None, int(qty), expiry_raw)
                self.editing_batch_id = None
                self.add_lote_btn.text = 'Adicionar lote'
                try:
                    self.add_lote_btn.update()
                except Exception:
                    pass
            self.reconstruir_tabela_lotes()
            # notificar caixa para atualizar opções e estoque exibido
            if self._product_refresh_cb:
                try:
                    self._product_refresh_cb()
                except Exception:
                    pass
        except Exception as ex:
            self.overlay.mostrar_mensagem('Erro', str(ex))

    def remover_lote_ui(self, bid):
        self.db.remover_lote(bid)
        self.reconstruir_tabela_lotes()
        if self._product_refresh_cb:
            try:
                self._product_refresh_cb()
            except Exception:
                pass

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
        # selecionar pelos nomes para evitar exibir ids no campo
        self.lote_product_dropdown.value = prod['nome'] if prod else None
        if b.get('fornecedor_id') and b.get('fornecedor_id') in self.db.fornecedores:
            s = self.db.fornecedores[b.get('fornecedor_id')]
            self.lote_supplier_dropdown.value = f"{s['nome']} — {s.get('descricao','')}" if s.get('descricao') else f"{s['nome']}"
        else:
            self.lote_supplier_dropdown.value = None
        self.lote_qty.value = str(b.get('quantidade'))
        try:
                # preencher day/month/year a partir do vencimento
                if b.get('vencimento'):
                    dt = b.get('vencimento')
                    try:
                        self.lote_day.value = str(dt.day)
                        self.lote_month.value = str(dt.month)
                        self.lote_year.value = str(dt.year)
                    except Exception:
                        pass
        except Exception:
            pass
        self.add_lote_btn.text = 'Salvar alterações'
        try:
            # atualizar controles para que a UI mostre os valores imediatamente
            try:
                self.lote_product_dropdown.update()
            except Exception:
                pass
            try:
                self.lote_supplier_dropdown.update()
            except Exception:
                pass
            try:
                self.lote_qty.update()
            except Exception:
                pass
            try:
                # atualizar os dropdowns de data (day/month/year)
                try:
                    self.lote_day.update()
                except Exception:
                    pass
                try:
                    self.lote_month.update()
                except Exception:
                    pass
                try:
                    self.lote_year.update()
                except Exception:
                    pass
            except Exception:
                pass
            self.add_lote_btn.update()
            self.page.update()
        except Exception:
            pass
