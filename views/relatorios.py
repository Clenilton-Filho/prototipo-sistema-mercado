import flet as ft
from datetime import datetime


class RelatoriosView:
    # --------------------- TELA: RELATÓRIOS ---------------------

    def __init__(self, page, db, overlay):
        self.page = page
        self.db = db
        self.overlay = overlay

        self.expired_table = ft.DataTable(columns=[
            ft.DataColumn(ft.Text('Lote ID')),
            ft.DataColumn(ft.Text('Produto')),
            ft.DataColumn(ft.Text('Quantidade')),
            ft.DataColumn(ft.Text('Vencimento')),
        ], rows=[])

        self.near_table = ft.DataTable(columns=[
            ft.DataColumn(ft.Text('Lote ID')),
            ft.DataColumn(ft.Text('Produto')),
            ft.DataColumn(ft.Text('Quantidade')),
            ft.DataColumn(ft.Text('Vence em (dias)')),
            ft.DataColumn(ft.Text('Desconto (%)')),
        ], rows=[])

        self.view = ft.Column([
            ft.Text('Relatórios diários'),
            ft.Row([ft.Button('Atualizar relatório', on_click=lambda e: self.reconstruir_relatorios())]),
            ft.Text('Produtos vencidos:'), ft.Column([self.expired_table], expand=True, scroll=ft.ScrollMode.AUTO),
            ft.Divider(),
            ft.Text('Produtos perto de vencer (desconto automático):'), ft.Column([self.near_table], expand=True, scroll=ft.ScrollMode.AUTO)
        ], expand=1)

    def reconstruir_relatorios(self):
        # Reconstroi os relatórios de lotes vencidos e próximos ao vencimento.
        # Esta função é chamada quando o usuário solicita atualização.
        self.expired_table.rows.clear()
        for b in self.db.produtos_vencidos():
            p = self.db.produtos.get(b.get('produto_id'))
            self.expired_table.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(str(b['id']))),
                ft.DataCell(ft.Text(p['nome'] if p else '')),
                ft.DataCell(ft.Text(str(b.get('quantidade')))),
                ft.DataCell(ft.Text(b.get('vencimento_raw') or '')),
            ]))
        self.near_table.rows.clear()
        for b in self.db.produtos_perto_vencimento():
            p = self.db.produtos.get(b.get('produto_id'))
            days_left = (b.get('vencimento') - datetime.today().date()).days if b.get('vencimento') else '-'
            discount = p.get('desconto_perto_vencimento', 0) if p else 0
            self.near_table.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(str(b['id']))),
                ft.DataCell(ft.Text(p['nome'] if p else '')),
                ft.DataCell(ft.Text(str(b.get('quantidade')))),
                ft.DataCell(ft.Text(str(days_left))),
                ft.DataCell(ft.Text(str(discount))),
            ]))
        self.page.update()

    def reconstruir(self):
        self.reconstruir_relatorios()
