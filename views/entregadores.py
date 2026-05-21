import flet as ft


class EntregadoresView:
    # --------------------- TELA: ENTREGADORES ---------------------

    def __init__(self, page, db, overlay, dropdown_entregador):
        self.page = page
        self.db = db
        self.overlay = overlay
        self.dropdown_entregador = dropdown_entregador

        self.campo_nome_entregador = ft.TextField(label='Nome entregador', width=300)

        self.btn_adicionar_entregador = ft.Button('Adicionar entregador')
        # estado de edição para entregadores
        self.id_entregador_editando = None

        self.tabela_entregadores = ft.DataTable(columns=[
            ft.DataColumn(ft.Text('ID')),
            ft.DataColumn(ft.Text('Nome')),
            ft.DataColumn(ft.Text('Pendentes')),
            ft.DataColumn(ft.Text('Ações')),
        ], rows=[])

        self.btn_adicionar_entregador.on_click = self.adicionar_entregador

        self.view = ft.Row([
            ft.Column([ft.Text('Entregadores'), ft.Column([self.tabela_entregadores], expand=True, scroll=ft.ScrollMode.AUTO)], expand=1),
            ft.VerticalDivider(width=20),
            ft.Column([ft.Text('Adicionar entregador'), self.campo_nome_entregador, self.btn_adicionar_entregador], width=420)
        ], expand=True)

    def reconstruir_tabela_entregadores(self):
        self.tabela_entregadores.rows.clear()
        for did, d in self.db.entregadores.items():
            cnt = self.db.contar_entregas_para(did)
            self.tabela_entregadores.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(str(did))),
                ft.DataCell(ft.Text(d['nome'])),
                ft.DataCell(ft.Text(str(cnt))),
                ft.DataCell(ft.Row([
                    ft.IconButton(ft.icons.Icons.DELETE, tooltip='Remover', on_click=lambda e, id=did: self.remove_deliverer(id)),
                    ft.IconButton(ft.icons.Icons.EDIT, tooltip='Editar', on_click=lambda e, id=did: self.start_edit_deliverer(id))
                ]))
            ]))
        # atualizar dropdown do caixa
        self.dropdown_entregador.options = [ft.dropdown.Option(d['nome']) for d in self.db.entregadores.values()]
        self.page.update()

    def reconstruir(self):
        self.reconstruir_tabela_entregadores()

    def adicionar_entregador(self, e):
        # adicionar_entregador: se não estivermos em modo de edição cria um
        # novo entregador; se estivermos, atualiza o entregador em edição.
        try:
            name = self.campo_nome_entregador.value.strip()
            if not name:
                self.overlay.mostrar_mensagem('Erro', 'Preencha o nome do entregador')
                return
            if self.id_entregador_editando is None:
                self.db.adicionar_entregador(name)
            else:
                self.db.atualizar_entregador(self.id_entregador_editando, name)
                self.id_entregador_editando = None
                self.btn_adicionar_entregador.text = 'Adicionar entregador'
                try:
                    self.btn_adicionar_entregador.update()
                except Exception:
                    pass
            self.campo_nome_entregador.value = ''
            self.reconstruir_tabela_entregadores()
        except Exception as ex:
            self.overlay.mostrar_mensagem('Erro', str(ex))

    def remove_deliverer(self, did):
        if did in self.db.entregadores:
            del self.db.entregadores[did]
        # cancelar edição se estava editando este entregador
        try:
            if self.id_entregador_editando == did:
                self.id_entregador_editando = None
                self.btn_adicionar_entregador.text = 'Adicionar entregador'
                try:
                    self.btn_adicionar_entregador.update()
                except Exception:
                    pass
        except Exception:
            pass
        self.reconstruir_tabela_entregadores()

    def start_edit_deliverer(self, did):
        d = self.db.entregadores.get(did)
        if not d:
            self.overlay.mostrar_mensagem('Erro', 'Entregador não encontrado')
            return
        self.id_entregador_editando = did
        self.campo_nome_entregador.value = d['nome']
        self.btn_adicionar_entregador.text = 'Salvar alterações'
        try:
            # garantir que o campo e botão sejam atualizados imediatamente
            self.campo_nome_entregador.update()
            self.btn_adicionar_entregador.update()
            try:
                # atualizar dropdowns que dependem da lista de entregadores
                self.dropdown_entregador.options = [ft.dropdown.Option(d['nome']) for d in self.db.entregadores.values()]
                self.dropdown_entregador.update()
            except Exception:
                pass
            self.page.update()
        except Exception:
            pass
