import flet as ft
from datetime import datetime
from utils import formatar_moeda


class CaixaView:
    # --------------------- TELA: CAIXA ---------------------
    # Elementos da tela de caixa
    # A tela de caixa contém:
    # - um seletor de produto + campo de quantidade + botão para adicionar
    # - uma lista expansível com os itens do carrinho (`cart_list`)
    # - um rodapé fixo com total e botões (Finalizar / Cancelar)

    def __init__(self, page, db, overlay, state):
        self.page = page
        self.db = db
        self.overlay = overlay
        self.state = state
        self.reconstruir_entregadores_callback = None

        self.product_dropdown = ft.Dropdown(label='Produto', hint_text='Selecione o produto', width=300, options=[ft.dropdown.Option(p['nome']) for p in db.produtos.values()])
        self.campo_qtd = ft.TextField(value='1', width=100)
        self.btn_adicionar_carrinho = ft.Button('Adicionar ao carrinho')

        self.lista_carrinho = ft.ListView(expand=1, spacing=5)
        self.texto_total = ft.Text('Total: R$ 0,00', size=18)

        self.btn_adicionar_carrinho.on_click = self.adicionar_ao_carrinho

        # Toggle de entrega
        self.btn_toggle_entrega = ft.Button('Entrega em casa: NÃO', on_click=lambda e: self.alternar_entrega())
        self.dropdown_entregador = ft.Dropdown(label='Entregador', width=250, options=[ft.dropdown.Option(d['nome']) for d in db.entregadores.values()])
        self.dropdown_entregador.visible = False
        self.info_entregador = ft.Text('')
        self.info_entregador.visible = False

        self.dropdown_entregador.on_change = lambda e: self.atualizar_info_entregador()

        # Banner de mensagem de venda — aparece ao finalizar e some ao fechar
        self.sale_msg_text = ft.Text('')
        self.sale_msg_row = ft.Row([self.sale_msg_text, ft.Button('Fechar', on_click=lambda e: (setattr(self.sale_msg_row, 'visible', False), self.sale_msg_row.update()))])
        self.sale_msg_row.visible = False

        self.cancel_btn = ft.Button('Cancelar venda', bgcolor=ft.Colors.RED_ACCENT_100, color=ft.Colors.WHITE, on_click=lambda e: self.cancelar_venda())

        # organizar: separar conteúdo principal (expand) do rodapé fixo
        self.bottom_row = ft.Row([self.texto_total, self.btn_toggle_entrega, self.dropdown_entregador, self.info_entregador, ft.Row([ft.Button('Finalizar venda', on_click=self.finalizar_venda), self.cancel_btn])], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        self.main_content = ft.Column([
            ft.Row([self.product_dropdown, self.campo_qtd, self.btn_adicionar_carrinho]),
            self.lista_carrinho,
            self.sale_msg_row
        ], expand=True)

        # Caixa_view com espaço entre main_content (expande) e bottom_row (fixo no rodapé)
        # `caixa_view` é a coluna principal da tela de caixa. A estrutura
        # separa `main_content` (expansível) do `bottom_row` (rodapé fixo),
        # garantindo que o rodapé fique sempre no fim da janela.
        self.view = ft.Column([
            self.main_content,
            self.bottom_row
        ], expand=True, alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    def reconstruir_lista_carrinho(self):
        # Reconstrói os controles que mostram os itens do carrinho.
        # Chamamos esta função sempre que o carrinho muda para atualizar a UI.
        self.lista_carrinho.controls.clear()
        total = 0.0
        for i, it in enumerate(self.state['cart']):
            quantidade = it.get('quantidade', it.get('qty', 0))
            preco_u = it.get('preco_unitario', it.get('unit_price', 0.0))
            line = ft.Row([
                ft.Text(f"{it.get('nome','')} x{quantidade}", expand=1),
                ft.Text(formatar_moeda(quantidade * preco_u)),
                ft.IconButton(ft.icons.Icons.DELETE, on_click=lambda e, idx=i: self.remover_item_carrinho(idx))
            ])
            self.lista_carrinho.controls.append(line)
            total += quantidade * preco_u
        self.texto_total.value = f'Total: {formatar_moeda(total)}'
        self.page.update()

    def remover_item_carrinho(self, idx):
        self.state['cart'].pop(idx)
        self.reconstruir_lista_carrinho()

    def adicionar_ao_carrinho(self, e):
        # Evento chamado quando o usuário clica em "Adicionar ao carrinho".
        # Valida seleção e quantidade, aplica desconto automático se houver
        # lote próximo do vencimento e então adiciona o item ao estado.
        sel = self.product_dropdown.value
        if not sel:
            self.overlay.mostrar_mensagem('Erro', 'Selecione um produto')
            return
        # encontrar produto por nome
        prod = next((p for p in self.db.produtos.values() if p['nome'] == sel), None)
        if not prod:
            self.overlay.mostrar_mensagem('Erro', 'Produto não encontrado')
            return
        try:
            q = int(self.campo_qtd.value)
        except Exception:
            self.overlay.mostrar_mensagem('Erro', 'Quantidade inválida')
            return
        # aplicar desconto automático se próximo do vencimento (busca lotes do produto)
        unit_price = prod['preco']
        # Verifica se existe lote próximo do vencimento e aplica desconto do produto
        for b in self.db.lotes:
            if b['produto_id'] == prod['id'] and b.get('vencimento'):
                days_left = (b['vencimento'] - datetime.today().date()).days
                if 0 <= days_left <= prod.get('dias_perto', 7):
                    discount = prod.get('desconto_perto_vencimento', 0.0)
                    unit_price = unit_price * (1 - discount / 100.0)
                    break
        self.state['cart'].append({'produto_id': prod['id'], 'quantidade': q, 'preco_unitario': unit_price, 'nome': prod['nome']})
        self.reconstruir_lista_carrinho()

    def atualizar_info_entregador(self):
        # mostra quantas entregas pendentes o entregador selecionado tem
        name = self.dropdown_entregador.value
        if not name:
            self.info_entregador.value = ''
        else:
            # encontra id do entregador
            did = next((i for i, dv in self.db.entregadores.items() if dv['nome'] == name), None)
            if did is None:
                self.info_entregador.value = ''
            else:
                cnt = self.db.contar_entregas_para(did)
                self.info_entregador.value = f'Entregas pendentes: {cnt}'
        self.info_entregador.update()

    # toggle_delivery: alterna o estado de entrega em casa.
    # - atualiza `state['delivery_enabled']`
    # - substitui a instância do botão `delivery_toggle` no layout por
    #   uma nova com o texto apropriado para forçar renderização em
    #   diferentes versões do Flet
    # - mostra/oculta `deliverer_dropdown` e `deliverer_info`
    def alternar_entrega(self):
        self.state['delivery_enabled'] = not self.state['delivery_enabled']
        # criar novo botão para garantir atualização visual
        new_btn = ft.Button(f"Entrega em casa: {'SIM' if self.state['delivery_enabled'] else 'NÃO'}", on_click=lambda e: self.alternar_entrega())
        # substituir no layout (texto_total, btn_toggle_entrega, dropdown_entregador, ...)
        try:
            self.bottom_row.controls[1] = new_btn
        except Exception:
            pass
        self.btn_toggle_entrega = new_btn
        self.dropdown_entregador.visible = self.state['delivery_enabled']
        self.info_entregador.visible = self.state['delivery_enabled']
        try:
            self.dropdown_entregador.update()
        except Exception:
            pass
        try:
            self.info_entregador.update()
        except Exception:
            pass
        try:
            self.btn_toggle_entrega.update()
        except Exception:
            pass
        self.page.update()

    def finalizar_venda(self, e):
        try:
            # debug: confirmar clique do botão (console + banner)
            print('DEBUG: finalize clicked')
            self.sale_msg_text.value = 'DEBUG: finalize clicado'
            self.sale_msg_row.visible = True
            self.sale_msg_text.update(); self.sale_msg_row.update()
            self.overlay.mostrar_mensagem('DEBUG', 'Finalizar clicado')
            if not self.state['cart']:
                self.overlay.mostrar_mensagem('Aviso', 'Carrinho vazio')
                return
            total = sum(it['quantidade'] * it['preco_unitario'] for it in self.state['cart'])

            # Debitar estoque: percorre os lotes do produto e decrementa a
            # quantidade (FIFO por vencimento). Esta lógica é propositalmente
            # simples para o exemplo acadêmico.
            for it in self.state['cart']:
                qty_left = it['quantidade']
                # ordenar lotes por data de vencimento crescente
                batches = sorted([b for b in self.db.lotes if b['produto_id'] == it['produto_id'] and b['quantidade'] > 0], key=lambda x: x.get('vencimento') or datetime.max.date())
                for b in batches:
                    if qty_left <= 0:
                        break
                    take = min(b['quantidade'], qty_left)
                    b['quantidade'] -= take
                    qty_left -= take

            # registrar entrega se for solicitado
            if self.state['delivery_enabled'] and self.dropdown_entregador.value:
                # encontra id do entregador selecionado
                did = next((i for i, dv in self.db.entregadores.items() if dv['nome'] == self.dropdown_entregador.value), None)
                if did is not None:
                    self.db.adicionar_entrega(did, total)
                    # atualiza tabela de entregadores
                    if self.reconstruir_entregadores_callback:
                        self.reconstruir_entregadores_callback()
                    self.atualizar_info_entregador()

            # montar conteúdo detalhado do diálogo com os itens e total
            content_list = [ft.Text('Itens da venda:')]
            for it in self.state['cart']:
                content_list.append(ft.Text(f"{it.get('nome', '')} x{it.get('quantidade', 0)} — {formatar_moeda(it.get('quantidade', 0) * it.get('preco_unitario', 0.0))}"))
            content_list.append(ft.Divider())
            content_list.append(ft.Text(f'Valor total: {formatar_moeda(total)}', weight=ft.FontWeight.BOLD))

            # função que será chamada quando o usuário fechar o modal de
            # finalização: fecha o overlay e limpa o estado da venda.
            def close_and_clear(ev=None):
                try:
                    self.overlay.fechar_overlay()
                except Exception:
                    pass
                self.limpar_estado_venda()

            # usar overlay customizado para o diálogo de finalização
            self.overlay.mostrar_overlay('Venda finalizada', ft.Column(content_list), on_close=close_and_clear)
        except Exception as ex:
            self.overlay.mostrar_mensagem('Erro ao finalizar', str(ex))
        except Exception as ex:
            self.overlay.mostrar_mensagem('Erro ao finalizar', str(ex))

    def fechar_dialogo_venda(self, ev):
        self.page.dialog.open = False
        # resetar carrinho e entrega
        self.state['cart'].clear()
        self.reconstruir_lista_carrinho()
        self.state['delivery_enabled'] = False
        self.btn_toggle_entrega.text = 'Entrega em casa: NÃO'
        self.dropdown_entregador.visible = False
        self.dropdown_entregador.value = None
        self.info_entregador.value = ''
        self.info_entregador.update()
        self.product_dropdown.value = None
        self.campo_qtd.value = '1'
        # esconder banner de mensagem
        self.sale_msg_row.visible = False
        self.sale_msg_row.update()
        self.page.update()

    def limpar_estado_venda(self):
        # Limpa tudo relacionado à venda (usado por cancelar e finalizar)
        self.state['cart'].clear()
        self.reconstruir_lista_carrinho()
        self.state['delivery_enabled'] = False
        self.btn_toggle_entrega.text = 'Entrega em casa: NÃO'
        try:
            self.btn_toggle_entrega.update()
        except Exception:
            pass
        self.dropdown_entregador.visible = False
        self.dropdown_entregador.value = None
        self.info_entregador.value = ''
        self.info_entregador.update()
        self.product_dropdown.value = None
        self.product_dropdown.update()
        self.campo_qtd.value = '1'
        try:
            self.campo_qtd.update()
        except Exception:
            pass
        self.sale_msg_row.visible = False
        self.sale_msg_row.update()

    def cancelar_venda(self):
        # limpa estado da venda e mostra confirmação
        self.limpar_estado_venda()
        dlg = ft.AlertDialog(title=ft.Text('Venda cancelada'), content=ft.Text('A venda foi cancelada e todos os campos foram limpos.'), modal=True, actions=[
            ft.TextButton('OK', on_click=lambda ev: (setattr(self.page.dialog, 'open', False), self.page.update()))
        ])
        self.page.dialog = dlg
        self.page.dialog.open = True
        self.page.update()
