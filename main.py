import flet as ft
from datetime import datetime, timedelta

# Para executar: `python main.py` (assume que o pacote `flet` está instalado).
# Se você nunca viu Flet: a função `main(page)` é o ponto de entrada. O
# objeto `page` representa a janela e você adiciona `controls` (widgets)
# a ele. Elementos como `ft.Column`, `ft.Row`, `ft.Button` e `ft.Text`
# compõem a interface. Muitas funções abaixo criam/atualizam controles e
# chamam `page.update()` para refletir mudanças na tela.

# Sistema simples em memória para um mercado (uso interno por funcionários)
# Arquitetura: um único arquivo para facilitar entendimento de iniciantes.
# Banco de dados em memória: dicionários e listas.


def formatar_moeda(v):
    return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# alias para compatibilidade com chamadas antigas
format_currency = formatar_moeda

class BancoMemoria:
    """Banco em memória. Estruturas simples:
    - products: {product_id: {name, code, price, discount_near_expiry, near_days}}
    - suppliers: {supplier_id: {name, products: {product_id: price}}}
    - batches: list of {id, product_id, supplier_id, quantity, expiry: date}
    - deliverers: {id: {name}}
    """

    def __init__(self):
        self.produtos = {}
        self.fornecedores = {}
        self.lotes = []
        self.entregas = []
        self.entregadores = {}
        self._pid = 1
        self._sid = 1
        self._bid = 1
        self._did = 1

    # Produtos
    def adicionar_produto(self, name, code, price, discount_near_expiry=0.0, near_days=7):
        # validações simples: nome e código únicos
        for p in self.produtos.values():
            if p['nome'].lower() == name.lower():
                raise ValueError('Nome de produto já existe')
            if p['codigo'] == code:
                raise ValueError('Código do produto já existe')
        pid = self._pid
        self.produtos[pid] = {
            'id': pid,
            'nome': name,
            'codigo': code,
            'preco': float(price),
            'desconto_perto_vencimento': float(discount_near_expiry),
            'dias_perto': int(near_days)
        }
        self._pid += 1
        return pid

    def atualizar_produto(self, product_id, name, code, price, discount_near_expiry=0.0, near_days=7):
        # update_product: atualiza os campos de um produto existente.
        # - valida unicidade de `name` e `code` entre os demais produtos
        # - converte valores para os tipos corretos
        # Usado pela UI quando o usuário edita um produto e clica em
        # "Salvar alterações" no formulário de cadastro.
        # atualiza um produto existente, mantendo validações de unicidade
        if product_id not in self.produtos:
            raise ValueError('Produto não encontrado')
        for pid, p in self.produtos.items():
            if pid == product_id:
                continue
            if p['nome'].lower() == name.lower():
                raise ValueError('Nome de produto já existe')
            if p['codigo'] == code:
                raise ValueError('Código do produto já existe')
        self.produtos[product_id].update({
            'nome': name,
            'codigo': code,
            'preco': float(price),
            'desconto_perto_vencimento': float(discount_near_expiry),
            'dias_perto': int(near_days)
        })

    def remover_produto(self, product_id):
        # remove_product: remove o produto do banco em memória e
        # limpa referências simples (ex.: preços em fornecedores).
        # Usado pela UI quando o usuário clica no ícone de lixeira na
        # tabela de produtos.
        # remove produto e quaisquer referências simples
        if product_id in self.produtos:
            del self.produtos[product_id]
            # remover preços em fornecedores que referenciam este produto
            for s in self.fornecedores.values():
                if product_id in s.get('produtos', {}):
                    try:
                        del s['produtos'][product_id]
                    except Exception:
                        pass

    # Fornecedores
    def adicionar_fornecedor(self, name):
        for s in self.fornecedores.values():
            if s['nome'].lower() == name.lower():
                raise ValueError('Nome de fornecedor já existe')
        sid = self._sid
        self.fornecedores[sid] = {'id': sid, 'nome': name, 'produtos': {}}
        self._sid += 1
        return sid

    def fornecedor_definir_preco(self, supplier_id, product_id, price):
        self.fornecedores[supplier_id]['produtos'][product_id] = float(price)

    # Lotes / estoque
    def adicionar_lote(self, product_id, supplier_id, quantity, expiry_date_str):
        bid = self._bid
        expiry = None
        try:
            expiry = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
        except Exception:
            expiry = None
        self.lotes.append({
            'id': bid,
            'produto_id': product_id,
            'fornecedor_id': supplier_id,
            'quantidade': int(quantity),
            'vencimento': expiry,
            'vencimento_raw': expiry_date_str,
        })
        self._bid += 1
        return bid

    def remover_lote(self, batch_id):
        self.lotes = [b for b in self.lotes if b['id'] != batch_id]

    def atualizar_lote(self, batch_id, product_id, supplier_id, quantity, expiry_date_str):
        # update_batch: atualiza os dados de um lote (batch).
        # Converte a data de string para `date` quando possível e
        # sobrescreve os campos do lote correspondente.
        # Usado pela UI ao editar um lote e salvar alterações.
        # atualiza um lote existente
        expiry = None
        try:
            expiry = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
        except Exception:
            expiry = None
        for b in self.lotes:
            if b['id'] == batch_id:
                b['produto_id'] = product_id
                b['fornecedor_id'] = supplier_id
                b['quantidade'] = int(quantity)
                b['vencimento'] = expiry
                b['vencimento_raw'] = expiry_date_str
                return

    # Entregadores
    def adicionar_entregador(self, name):
        for d in self.entregadores.values():
            if d['nome'].lower() == name.lower():
                raise ValueError('Nome de entregador já existe')
        did = self._did
        self.entregadores[did] = {'id': did, 'nome': name}
        self._did += 1
        return did

    def atualizar_entregador(self, deliverer_id, name):
        # update_deliverer: atualiza o nome de um entregador,
        # garantindo que não haja duplicatas.
        # Usado pela UI quando o usuário edita um entregador e salva.
        # atualiza nome do entregador com validação de unicidade
        if deliverer_id not in self.entregadores:
            raise ValueError('Entregador não encontrado')
        for did, d in self.entregadores.items():
            if did == deliverer_id:
                continue
            if d['nome'].lower() == name.lower():
                raise ValueError('Nome de entregador já existe')
        self.entregadores[deliverer_id]['nome'] = name

    def adicionar_entrega(self, deliverer_id, total):
        # adiciona entrega pendente para o entregador
        did = len(self.entregas) + 1
        self.entregas.append({'id': did, 'entregador_id': deliverer_id, 'valor_total': float(total), 'status': 'pending'})
        return did

    def contar_entregas_para(self, deliverer_id):
        return sum(1 for d in self.entregas if d['entregador_id'] == deliverer_id and d['status'] == 'pending')

    # estoque atual calculado a partir dos lotes
    def estoque_atual(self):
        stock = {}
        for b in self.lotes:
            pid = b['produto_id']
            stock[pid] = stock.get(pid, 0) + b['quantidade']
        return stock

    def produtos_vencidos(self):
        today = datetime.today().date()
        expired = []
        for b in self.lotes:
            if b['vencimento'] and b['vencimento'] < today and b['quantidade'] > 0:
                expired.append(b)
        return expired

    def produtos_perto_vencimento(self):
        today = datetime.today().date()
        near = []
        for b in self.lotes:
            if b['vencimento']:
                prod = self.produtos.get(b['produto_id'])
                ndays = prod.get('dias_perto', 7)
                if 0 <= (b['vencimento'] - today).days <= ndays:
                    near.append(b)
        return near


db = BancoMemoria()

# Preencher com alguns dados de exemplo para o relatório padrão
pid1 = db.adicionar_produto('Arroz 5kg', 'ARZ5', 25.0, discount_near_expiry=20.0, near_days=5)
pid2 = db.adicionar_produto('Feijão 1kg', 'FJ1', 8.0, discount_near_expiry=10.0, near_days=7)
sid1 = db.adicionar_fornecedor('Fornecedor A')
db.fornecedor_definir_preco(sid1, pid1, 23.0)
db.fornecedor_definir_preco(sid1, pid2, 7.5)
db.adicionar_lote(pid1, sid1, 10, (datetime.today() + timedelta(days=2)).strftime('%Y-%m-%d'))
db.adicionar_lote(pid2, sid1, 5, (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d'))
did1 = db.adicionar_entregador('Entregador 1')


def main(page: ft.Page):
    # Configurações iniciais da página
    page.title = 'Projeto Mercado - Caixa'
    page.theme_mode = 'light'  # tema claro
    page.window_maximized = True

    # `page` é a janela principal da aplicação. Aqui configuramos título,
    # tema e estado inicial da janela. A partir daqui criamos os controles
    # (widgets) e funções que reagem a eventos (cliques, mudanças de valor).

    # Estado da aplicação
    state = {
        'current_screen': 'caixa',
        'cart': [],  # itens: {product_id, qty, unit_price, name}
        'delivery_enabled': False,
        'selected_deliverer': None,
    }
    # id do fornecedor atualmente selecionado na tela de fornecedores
    selected_supplier_id = None

    # Funções utilitárias UI
    def atualizar_top_bar():
        # nada dinâmico aqui por enquanto
        pass

    # Overlay modal customizado (fallback caso AlertDialog não apareça)
    # Variáveis usadas para o overlay (janela modal que fica sobre a UI).
    # Mantemos `overlay_box` para poder remover/fechar o modal depois.
    overlay_box = None
    overlay_mode = None
    main_stack = ft.Stack(expand=True)

    def fechar_overlay(e=None):
        nonlocal overlay_box, overlay_mode
        try:
            if overlay_box:
                if overlay_mode == 'positioned':
                    if overlay_box in main_stack.controls:
                        main_stack.controls.remove(overlay_box)
                elif overlay_mode == 'page_overlay':
                    try:
                        if hasattr(page, 'overlay') and overlay_box in page.overlay:
                            page.overlay.remove(overlay_box)
                    except Exception:
                        pass
                else:
                    # fallback: remove from main_stack if present
                    if overlay_box in main_stack.controls:
                        main_stack.controls.remove(overlay_box)
            overlay_box = None
            overlay_mode = None
            page.update()
        except Exception:
            pass

    def mostrar_overlay(title, content_control, on_close=None):
        nonlocal overlay_box, overlay_mode
        # remove overlay anterior se existir
        fechar_overlay()

        # botão de fechar que chama um callback opcional além de fechar o overlay
        def _on_close(e=None):
            try:
                fechar_overlay()
            except Exception:
                pass
            try:
                if on_close:
                    on_close()
            except Exception:
                pass

        # O 'card' é o painel central do modal. O conteúdo (lista de itens
        # ou mensagem) é passado via `content_control`. O botão 'Fechar'
        # chama `_on_close` que fecha o overlay e (opcionalmente) executa
        # um callback passado por `on_close`.
        card = ft.Container(
            content=ft.Column([
                ft.Text(title, weight=ft.FontWeight.BOLD, size=18),
                ft.Divider(),
                content_control,
                ft.Divider(),
                ft.Row([ft.Button('Fechar', on_click=_on_close)], alignment=ft.MainAxisAlignment.END)
            ], tight=True),
            width=560,
            padding=20,
            bgcolor=ft.Colors.WHITE,
            border_radius=8
        )

        # criar o overlay (conteúdo escuro + cartão central)
        overlay_full = ft.Container(
            content=ft.Column([ft.Row([card], alignment=ft.MainAxisAlignment.CENTER)], alignment=ft.MainAxisAlignment.CENTER),
            expand=True,
            bgcolor=ft.Colors.BLACK45
        )

        # Monta o overlay escuro que cobre a tela e centraliza o card.
        # Aqui tentamos usar diferentes mecanismos dependendo da versão do
        # Flet (Positioned, page.overlay ou fallback para anexar ao stack).
        # Isso é necessário porque a API do Flet pode variar entre versões.
        try:
            if hasattr(ft, 'Positioned'):
                overlay_box = ft.Positioned(left=0, top=0, right=0, bottom=0, child=overlay_full)
                overlay_mode = 'positioned'
                main_stack.controls.append(overlay_box)
            elif hasattr(page, 'overlay'):
                # usar API page.overlay quando disponível
                overlay_box = overlay_full
                overlay_mode = 'page_overlay'
                page.overlay.append(overlay_box)
            else:
                # fallback simples: anexar container ao main_stack
                overlay_box = overlay_full
                overlay_mode = 'stack_fallback'
                main_stack.controls.append(overlay_box)
        except Exception:
            # último recurso: anexar ao main_stack
            overlay_box = overlay_full
            overlay_mode = 'stack_fallback'
            try:
                main_stack.controls.append(overlay_box)
            except Exception:
                pass

        page.update()

    def mostrar_mensagem(title, content):
        # usa overlay customizado para garantir visibilidade no ambiente do usuário
        try:
            print(f"DEBUG mostrar_mensagem called: {title} | {content}")
            mostrar_overlay(title, ft.Text(content))
            print('DEBUG mostrar_mensagem: overlay appended')
        except Exception as ex:
            print('DEBUG mostrar_mensagem failed:', ex)

    # Observação sobre mensagens: durante desenvolvimento usamos `print`
    # para debug; antes de entregar/remover estes prints, substitua por
    # logs ou remova para não poluir o console do usuário.

    # --------------------- TELA: CAIXA ---------------------
    # Elementos da tela de caixa
    # A tela de caixa contém:
    # - um seletor de produto + campo de quantidade + botão para adicionar
    # - uma lista expansível com os itens do carrinho (`cart_list`)
    # - um rodapé fixo com total e botões (Finalizar / Cancelar)
    product_dropdown = ft.Dropdown(label='Produto', hint_text='Selecione o produto', width=300, options=[ft.dropdown.Option(p['nome']) for p in db.produtos.values()])
    campo_qtd = ft.TextField(value='1', width=100)
    btn_adicionar_carrinho = ft.Button('Adicionar ao carrinho')

    lista_carrinho = ft.ListView(expand=1, spacing=5)
    texto_total = ft.Text('Total: R$ 0,00', size=18)

    def reconstruir_lista_carrinho():
        # Reconstrói os controles que mostram os itens do carrinho.
        # Chamamos esta função sempre que o carrinho muda para atualizar a UI.
        lista_carrinho.controls.clear()
        total = 0.0
        for i, it in enumerate(state['cart']):
            quantidade = it.get('quantidade', it.get('qty', 0))
            preco_u = it.get('preco_unitario', it.get('unit_price', 0.0))
            line = ft.Row([
                ft.Text(f"{it.get('nome','')} x{quantidade}", expand=1),
                ft.Text(formatar_moeda(quantidade * preco_u)),
                ft.IconButton(ft.icons.Icons.DELETE, on_click=lambda e, idx=i: remover_item_carrinho(idx))
            ])
            lista_carrinho.controls.append(line)
            total += quantidade * preco_u
        texto_total.value = f'Total: {formatar_moeda(total)}'
        page.update()

    def remover_item_carrinho(idx):
        state['cart'].pop(idx)
        reconstruir_lista_carrinho()

    def adicionar_ao_carrinho(e):
        # Evento chamado quando o usuário clica em "Adicionar ao carrinho".
        # Valida seleção e quantidade, aplica desconto automático se houver
        # lote próximo do vencimento e então adiciona o item ao estado.
        sel = product_dropdown.value
        if not sel:
            mostrar_mensagem('Erro', 'Selecione um produto')
            return
        # encontrar produto por nome
        prod = next((p for p in db.produtos.values() if p['nome'] == sel), None)
        if not prod:
            mostrar_mensagem('Erro', 'Produto não encontrado')
            return
        try:
            q = int(campo_qtd.value)
        except Exception:
            mostrar_mensagem('Erro', 'Quantidade inválida')
            return
        # aplicar desconto automático se próximo do vencimento (busca lotes do produto)
        unit_price = prod['preco']
        # Verifica se existe lote próximo do vencimento e aplica desconto do produto
        for b in db.lotes:
            if b['produto_id'] == prod['id'] and b.get('vencimento'):
                days_left = (b['vencimento'] - datetime.today().date()).days
                if 0 <= days_left <= prod.get('dias_perto', 7):
                    discount = prod.get('desconto_perto_vencimento', 0.0)
                    unit_price = unit_price * (1 - discount / 100.0)
                    break
        state['cart'].append({'produto_id': prod['id'], 'quantidade': q, 'preco_unitario': unit_price, 'nome': prod['nome']})
        reconstruir_lista_carrinho()

    btn_adicionar_carrinho.on_click = adicionar_ao_carrinho

    # Toggle de entrega
    btn_toggle_entrega = ft.Button('Entrega em casa: NÃO', on_click=lambda e: alternar_entrega())
    dropdown_entregador = ft.Dropdown(label='Entregador', width=250, options=[ft.dropdown.Option(d['nome']) for d in db.entregadores.values()])
    dropdown_entregador.visible = False
    info_entregador = ft.Text('')
    info_entregador.visible = False

    def atualizar_info_entregador():
        # mostra quantas entregas pendentes o entregador selecionado tem
        name = dropdown_entregador.value
        if not name:
            info_entregador.value = ''
        else:
            # encontra id do entregador
            did = next((i for i, dv in db.entregadores.items() if dv['nome'] == name), None)
            if did is None:
                info_entregador.value = ''
            else:
                cnt = db.contar_entregas_para(did)
                info_entregador.value = f'Entregas pendentes: {cnt}'
        info_entregador.update()

    dropdown_entregador.on_change = lambda e: atualizar_info_entregador()

    # toggle_delivery: alterna o estado de entrega em casa.
    # - atualiza `state['delivery_enabled']`
    # - substitui a instância do botão `delivery_toggle` no layout por
    #   uma nova com o texto apropriado para forçar renderização em
    #   diferentes versões do Flet
    # - mostra/oculta `deliverer_dropdown` e `deliverer_info`
    def alternar_entrega():
        nonlocal btn_toggle_entrega
        state['delivery_enabled'] = not state['delivery_enabled']
        # criar novo botão para garantir atualização visual
        new_btn = ft.Button(f"Entrega em casa: {'SIM' if state['delivery_enabled'] else 'NÃO'}", on_click=lambda e: alternar_entrega())
        # substituir no layout (texto_total, btn_toggle_entrega, dropdown_entregador, ...)
        try:
            bottom_row.controls[1] = new_btn
        except Exception:
            pass
        btn_toggle_entrega = new_btn
        dropdown_entregador.visible = state['delivery_enabled']
        info_entregador.visible = state['delivery_enabled']
        try:
            dropdown_entregador.update()
        except Exception:
            pass
        try:
            info_entregador.update()
        except Exception:
            pass
        try:
            btn_toggle_entrega.update()
        except Exception:
            pass
        page.update()

    def finalizar_venda(e):
        try:
            # debug: confirmar clique do botão (console + banner)
            print('DEBUG: finalize clicked')
            sale_msg_text.value = 'DEBUG: finalize clicado'
            sale_msg_row.visible = True
            sale_msg_text.update(); sale_msg_row.update()
            mostrar_mensagem('DEBUG', 'Finalizar clicado')
            if not state['cart']:
                mostrar_mensagem('Aviso', 'Carrinho vazio')
                return
            total = sum(it['quantidade'] * it['preco_unitario'] for it in state['cart'])

            # Debitar estoque: percorre os lotes do produto e decrementa a
            # quantidade (FIFO por vencimento). Esta lógica é propositalmente
            # simples para o exemplo acadêmico.
            for it in state['cart']:
                qty_left = it['quantidade']
                # ordenar lotes por data de vencimento crescente
                batches = sorted([b for b in db.lotes if b['produto_id'] == it['produto_id'] and b['quantidade'] > 0], key=lambda x: x.get('vencimento') or datetime.max.date())
                for b in batches:
                    if qty_left <= 0:
                        break
                    take = min(b['quantidade'], qty_left)
                    b['quantidade'] -= take
                    qty_left -= take

            # registrar entrega se for solicitado
            if state['delivery_enabled'] and dropdown_entregador.value:
                # encontra id do entregador selecionado
                did = next((i for i, dv in db.entregadores.items() if dv['nome'] == dropdown_entregador.value), None)
                if did is not None:
                    db.adicionar_entrega(did, total)
                    # atualiza tabela de entregadores
                    reconstruir_tabela_entregadores()
                    atualizar_info_entregador()

            # montar conteúdo detalhado do diálogo com os itens e total
            content_list = [ft.Text('Itens da venda:')]
            for it in state['cart']:
                content_list.append(ft.Text(f"{it.get('nome', '')} x{it.get('quantidade', 0)} — {formatar_moeda(it.get('quantidade', 0) * it.get('preco_unitario', 0.0))}"))
            content_list.append(ft.Divider())
            content_list.append(ft.Text(f'Valor total: {formatar_moeda(total)}', weight=ft.FontWeight.BOLD))

            # função que será chamada quando o usuário fechar o modal de
            # finalização: fecha o overlay e limpa o estado da venda.
            def close_and_clear(ev=None):
                try:
                    fechar_overlay()
                except Exception:
                    pass
                limpar_estado_venda()

            # usar overlay customizado para o diálogo de finalização
            mostrar_overlay('Venda finalizada', ft.Column(content_list), on_close=close_and_clear)
        except Exception as ex:
            mostrar_mensagem('Erro ao finalizar', str(ex))
        except Exception as ex:
            mostrar_mensagem('Erro ao finalizar', str(ex))

    def fechar_dialogo_venda(ev):
        page.dialog.open = False
        # resetar carrinho e entrega
        state['cart'].clear()
        reconstruir_lista_carrinho()
        state['delivery_enabled'] = False
        btn_toggle_entrega.text = 'Entrega em casa: NÃO'
        dropdown_entregador.visible = False
        dropdown_entregador.value = None
        info_entregador.value = ''
        info_entregador.update()
        product_dropdown.value = None
        campo_qtd.value = '1'
        # esconder banner de mensagem
        sale_msg_row.visible = False
        sale_msg_row.update()
        page.update()

    def limpar_estado_venda():
        # Limpa tudo relacionado à venda (usado por cancelar e finalizar)
        state['cart'].clear()
        reconstruir_lista_carrinho()
        state['delivery_enabled'] = False
        btn_toggle_entrega.text = 'Entrega em casa: NÃO'
        try:
            btn_toggle_entrega.update()
        except Exception:
            pass
        dropdown_entregador.visible = False
        dropdown_entregador.value = None
        info_entregador.value = ''
        info_entregador.update()
        product_dropdown.value = None
        product_dropdown.update()
        campo_qtd.value = '1'
        try:
            campo_qtd.update()
        except Exception:
            pass
        sale_msg_row.visible = False
        sale_msg_row.update()

    def cancelar_venda():
        # limpa estado da venda e mostra confirmação
        limpar_estado_venda()
        dlg = ft.AlertDialog(title=ft.Text('Venda cancelada'), content=ft.Text('A venda foi cancelada e todos os campos foram limpos.'), modal=True, actions=[
            ft.TextButton('OK', on_click=lambda ev: (setattr(page.dialog, 'open', False), page.update()))
        ])
        page.dialog = dlg
        page.dialog.open = True
        page.update()

    # Banner de mensagem de venda — aparece ao finalizar e some ao fechar
    sale_msg_text = ft.Text('')
    sale_msg_row = ft.Row([sale_msg_text, ft.Button('Fechar', on_click=lambda e: (setattr(sale_msg_row, 'visible', False), sale_msg_row.update()))])
    sale_msg_row.visible = False

    cancel_btn = ft.Button('Cancelar venda', bgcolor=ft.Colors.RED_ACCENT_100, color=ft.Colors.WHITE, on_click=lambda e: cancelar_venda())

    # organizar: separar conteúdo principal (expand) do rodapé fixo
    bottom_row = ft.Row([texto_total, btn_toggle_entrega, dropdown_entregador, info_entregador, ft.Row([ft.Button('Finalizar venda', on_click=finalizar_venda), cancel_btn])], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    main_content = ft.Column([
        ft.Row([product_dropdown, campo_qtd, btn_adicionar_carrinho]),
        lista_carrinho,
        sale_msg_row
    ], expand=True)

    # Caixa_view com espaço entre main_content (expande) e bottom_row (fixo no rodapé)
    # `caixa_view` é a coluna principal da tela de caixa. A estrutura
    # separa `main_content` (expansível) do `bottom_row` (rodapé fixo),
    # garantindo que o rodapé fique sempre no fim da janela.
    caixa_view = ft.Column([
        main_content,
        bottom_row
    ], expand=True, alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    # --------------------- TELA: PRODUTOS ---------------------
    # A tela de produtos permite cadastrar novos produtos e ver a lista
    # com preços formatados. A função `rebuild_products_list` reconstrói
    # a `DataTable` usada para exibir os produtos.
    campo_nome_prod = ft.TextField(label='Nome', width=300)
    campo_codigo_prod = ft.TextField(label='Código (único)', width=200)
    campo_preco_prod = ft.TextField(label='Preço', value='0.0', width=150)
    campo_desconto_prod = ft.TextField(label='Desconto perto venc. (%)', value='0', width=150)
    campo_dias_perto = ft.TextField(label='Dias para considerar perto', value='7', width=150)
    btn_cadastrar_produto = ft.Button('Cadastrar produto')
    # id do produto sendo editado (None quando cadastro novo)
    id_produto_editando = None

    tabela_produtos = ft.DataTable(columns=[
        ft.DataColumn(ft.Text('ID')),
        ft.DataColumn(ft.Text('Nome')),
        ft.DataColumn(ft.Text('Código')),
        ft.DataColumn(ft.Text('Preço')),
        ft.DataColumn(ft.Text('Desconto (%)')),
        ft.DataColumn(ft.Text('Perto (dias)')),
        ft.DataColumn(ft.Text('Ações')),
    ], rows=[])

    def reconstruir_lista_produtos():
        tabela_produtos.rows.clear()
        for p in db.produtos.values():
            tabela_produtos.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(str(p['id']))),
                ft.DataCell(ft.Text(p['nome'])),
                ft.DataCell(ft.Text(p['codigo'])),
                ft.DataCell(ft.Text(formatar_moeda(p['preco']))),
                ft.DataCell(ft.Text(str(p.get('desconto_perto_vencimento', 0)))),
                ft.DataCell(ft.Text(str(p.get('dias_perto', 7)))),
                ft.DataCell(ft.Row([
                    ft.IconButton(ft.icons.Icons.DELETE, tooltip='Remover', on_click=lambda e, pid=p['id']: remover_produto(pid)),
                    ft.IconButton(ft.icons.Icons.EDIT, tooltip='Editar', on_click=lambda e, pid=p['id']: iniciar_edicao_produto(pid))
                ]))
            ]))
        page.update()

    def selecionar_produto(name: str):
        # Função utilitária para selecionar um produto no dropdown do caixa
        product_dropdown.value = name
        product_dropdown.update()

    def remover_produto(pid):
        # remover_produto (UI handler): chama o DB para remover o produto
        # e atualiza dropdowns/tabelas; também cancela qualquer edição
        # em andamento se o produto removido estiver sendo editado.
        nonlocal id_produto_editando
        try:
            db.remover_produto(pid)
        except Exception as ex:
            mostrar_mensagem('Erro', str(ex))
            return
        # atualizar lista e dropdowns
        reconstruir_lista_produtos()
        try:
            product_dropdown.options = [ft.dropdown.Option(p['nome']) for p in db.produtos.values()]
            product_dropdown.update()
        except Exception:
            pass
        if id_produto_editando == pid:
            # cancelar edição se estava editando este produto
            id_produto_editando = None
            btn_cadastrar_produto.text = 'Cadastrar produto'
            try:
                btn_cadastrar_produto.update()
            except Exception:
                pass

    def iniciar_edicao_produto(pid):
        # iniciar_edicao_produto: pré-preenche o formulário de cadastro com
        # os dados do produto selecionado para edição e troca o texto
        # do botão para 'Salvar alterações'.
        nonlocal id_produto_editando
        p = db.produtos.get(pid)
        if not p:
            mostrar_mensagem('Erro', 'Produto não encontrado')
            return
        id_produto_editando = pid
        campo_nome_prod.value = p['nome']
        campo_codigo_prod.value = p['codigo']
        campo_preco_prod.value = str(p['preco'])
        campo_desconto_prod.value = str(p.get('desconto_perto_vencimento', 0))
        campo_dias_perto.value = str(p.get('dias_perto', 7))
        btn_cadastrar_produto.text = 'Salvar alterações'
        try:
            btn_cadastrar_produto.update()
        except Exception:
            pass

    def cadastrar_produto(e):
        # cadastrar_produto: handler do botão de cadastrar/salvar produto.
        # Se `id_produto_editando` for None, cria um novo produto.
        # Caso contrário, atualiza o produto em edição.
        try:
            nonlocal id_produto_editando
            name = campo_nome_prod.value.strip()
            code = campo_codigo_prod.value.strip()
            price = float(campo_preco_prod.value)
            discount = float(campo_desconto_prod.value)
            near_days = int(campo_dias_perto.value)
            if id_produto_editando is None:
                db.adicionar_produto(name, code, price, discount, near_days)
            else:
                db.atualizar_produto(id_produto_editando, name, code, price, discount, near_days)
                id_produto_editando = None
                btn_cadastrar_produto.text = 'Cadastrar produto'
                try:
                    btn_cadastrar_produto.update()
                except Exception:
                    pass
            campo_nome_prod.value = ''
            campo_codigo_prod.value = ''
            campo_preco_prod.value = '0.0'
            campo_desconto_prod.value = '0'
            campo_dias_perto.value = '7'
            reconstruir_lista_produtos()
            # atualizar dropdown do caixa
            product_dropdown.options = [ft.dropdown.Option(p['nome']) for p in db.produtos.values()]
            try:
                product_dropdown.update()
            except Exception:
                pass
            page.update()
        except Exception as ex:
            mostrar_mensagem('Erro ao cadastrar', str(ex))

    btn_cadastrar_produto.on_click = cadastrar_produto

    products_view = ft.Row([
        # coluna de cadastro com espaçamento maior entre campos
        ft.Column([ft.Text('Cadastrar produto'), campo_nome_prod, campo_codigo_prod, campo_preco_prod, campo_desconto_prod, campo_dias_perto, btn_cadastrar_produto], width=450, spacing=10),
        ft.VerticalDivider(width=20),
        ft.Column([ft.Text('Produtos cadastrados'), tabela_produtos], expand=1)
    ], expand=True, alignment=ft.MainAxisAlignment.CENTER)

    # --------------------- TELA: FORNECEDORES ---------------------
    # lado a lado: lista de fornecedores e formulário de adicionar
    lista_fornecedores = ft.ListView(width=300, spacing=5)
    campo_nome_fornecedor = ft.TextField(label='Nome fornecedor', width=300)
    btn_adicionar_fornecedor = ft.Button('Adicionar fornecedor')

    # Formulário para atribuir produtos a um fornecedor (na área de "Adicionar fornecedor")
    dropdown_fornecedor_atribuir = ft.Dropdown(label='Fornecedor (atribuir)', width=300, options=[ft.dropdown.Option(s['nome']) for s in db.fornecedores.values()])
    dropdown_produto_fornecedor_novo = ft.Dropdown(label='Produto', width=250, options=[ft.dropdown.Option(p['nome']) for p in db.produtos.values()])
    campo_preco_fornecedor_novo = ft.TextField(label='Preço do fornecedor', value='0.0', width=150)
    btn_atribuir_ao_fornecedor = ft.Button('Atribuir produto ao fornecedor')

    # Formulário que aparece dentro da área de detalhes do fornecedor selecionado
    dropdown_produto_fornecedor_selecionado = ft.Dropdown(label='Produto', width=250, options=[ft.dropdown.Option(p['nome']) for p in db.produtos.values()])
    campo_preco_fornecedor_selecionado = ft.TextField(label='Preço do fornecedor', value='0.0', width=150)
    btn_atribuir_selecionado = ft.Button('Atribuir a este fornecedor')

    detalhes_fornecedor = ft.Column()  # mostrará o que o fornecedor vende e o formulário de atribuição
    tabela_produtos_fornecedor = ft.DataTable(columns=[
        ft.DataColumn(ft.Text('Produto')),
        ft.DataColumn(ft.Text('Preço')),
    ], rows=[])

    def reconstruir_lista_fornecedores():
        lista_fornecedores.controls.clear()
        for s in db.fornecedores.values():
            lista_fornecedores.controls.append(ft.Row([
                ft.Text(s['nome'], expand=1),
                ft.TextButton('Ver', on_click=lambda e, sid=s['id']: selecionar_fornecedor(sid))
            ]))
        # atualizar dropdowns de seleção
        dropdown_fornecedor_atribuir.options = [ft.dropdown.Option(s['nome']) for s in db.fornecedores.values()]
        dropdown_produto_fornecedor_novo.options = [ft.dropdown.Option(p['nome']) for p in db.produtos.values()]
        dropdown_produto_fornecedor_selecionado.options = [ft.dropdown.Option(p['nome']) for p in db.produtos.values()]
        page.update()

    def selecionar_fornecedor(sid):
        nonlocal selected_supplier_id
        selected_supplier_id = sid
        s = db.fornecedores[sid]
        detalhes_fornecedor.controls.clear()
        detalhes_fornecedor.controls.append(ft.Text(f"Fornecedor: {s['nome']}"))
        detalhes_fornecedor.controls.append(ft.Divider())
        detalhes_fornecedor.controls.append(ft.Text('Atribuir produto a este fornecedor'))
        detalhes_fornecedor.controls.append(dropdown_produto_fornecedor_selecionado)
        detalhes_fornecedor.controls.append(campo_preco_fornecedor_selecionado)
        detalhes_fornecedor.controls.append(btn_atribuir_selecionado)
        detalhes_fornecedor.controls.append(ft.Divider())
        tabela_produtos_fornecedor.rows.clear()
        for pid, price in s['produtos'].items():
            p = db.produtos.get(pid)
            tabela_produtos_fornecedor.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(p['nome'] if p else '')),
                ft.DataCell(ft.Text(formatar_moeda(price)))
            ]))
        detalhes_fornecedor.controls.append(tabela_produtos_fornecedor)
        page.update()

    def atribuir_para_fornecedor_do_meio(e):
        sup_name = dropdown_fornecedor_atribuir.value
        prod_name_local = dropdown_produto_fornecedor_novo.value
        if not sup_name or not prod_name_local:
            mostrar_mensagem('Erro', 'Selecione fornecedor e produto')
            return
        sid = next((i for i, sv in db.fornecedores.items() if sv['nome'] == sup_name), None)
        prod = next((p for p in db.produtos.values() if p['nome'] == prod_name_local), None)
        if sid is None or prod is None:
            mostrar_mensagem('Erro', 'Fornecedor ou produto inválido')
            return
        try:
            db.fornecedor_definir_preco(sid, prod['id'], float(campo_preco_fornecedor_novo.value))
            reconstruir_lista_fornecedores()
            if selected_supplier_id == sid:
                selecionar_fornecedor(sid)
        except Exception as ex:
            mostrar_mensagem('Erro', str(ex))

    def atribuir_para_fornecedor_selecionado(e):
        if selected_supplier_id is None:
            mostrar_mensagem('Erro', 'Selecione um fornecedor (Ver)')
            return
        prod_name_local = dropdown_produto_fornecedor_selecionado.value
        if not prod_name_local:
            mostrar_mensagem('Erro', 'Selecione um produto')
            return
        prod = next((p for p in db.produtos.values() if p['nome'] == prod_name_local), None)
        try:
            db.fornecedor_definir_preco(selected_supplier_id, prod['id'], float(campo_preco_fornecedor_selecionado.value))
            selecionar_fornecedor(selected_supplier_id)
            reconstruir_lista_fornecedores()
        except Exception as ex:
            mostrar_mensagem('Erro', str(ex))

    def adicionar_fornecedor(e):
        try:
            sid = db.adicionar_fornecedor(campo_nome_fornecedor.value.strip())
            # se preencher produto no formulário de criação, já atribui
            if dropdown_produto_fornecedor_novo.value:
                prod = next((p for p in db.produtos.values() if p['nome'] == dropdown_produto_fornecedor_novo.value), None)
                if prod:
                    try:
                        db.fornecedor_definir_preco(sid, prod['id'], float(campo_preco_fornecedor_novo.value))
                    except Exception:
                        pass
            campo_nome_fornecedor.value = ''
            dropdown_produto_fornecedor_novo.value = None
            campo_preco_fornecedor_novo.value = '0.0'
            reconstruir_lista_fornecedores()
            # selecionar o novo fornecedor no dropdown de atribuição
            if db.fornecedores:
                last_sid = max(db.fornecedores.keys())
                dropdown_fornecedor_atribuir.value = db.fornecedores[last_sid]['nome']
                dropdown_fornecedor_atribuir.update()
            page.update()
        except Exception as ex:
            mostrar_mensagem('Erro ao cadastrar fornecedor', str(ex))

    btn_adicionar_fornecedor.on_click = adicionar_fornecedor
    btn_atribuir_ao_fornecedor.on_click = atribuir_para_fornecedor_do_meio
    btn_atribuir_selecionado.on_click = atribuir_para_fornecedor_selecionado

    suppliers_view = ft.Row([
        # esquerda: formulário de cadastro/atribuição (antes estava no meio)
        ft.Column([ft.Text('Adicionar fornecedor'), campo_nome_fornecedor, btn_adicionar_fornecedor, ft.Divider(), ft.Text('Atribuir produto a fornecedor (selecionar fornecedor)'), dropdown_fornecedor_atribuir, dropdown_produto_fornecedor_novo, campo_preco_fornecedor_novo, btn_atribuir_ao_fornecedor], width=420),
        ft.VerticalDivider(width=20),
        # centro: lista de fornecedores (label atualizado)
        ft.Column([ft.Text('Fornecedores - clique para mais detalhes'), lista_fornecedores], width=320),
        ft.VerticalDivider(width=20),
        # direita: detalhes do fornecedor
        ft.Column([ft.Text('Detalhes do fornecedor'), detalhes_fornecedor], expand=1)
    ], expand=True)

    # --------------------- TELA: ADD LOTE (ESTOQUE) ---------------------
    lote_product_dropdown = ft.Dropdown(options=[ft.dropdown.Option(p['nome']) for p in db.produtos.values()], hint_text='Selecione o produto')
    lote_supplier_dropdown = ft.Dropdown(options=[ft.dropdown.Option(s['nome']) for s in db.fornecedores.values()], hint_text='Fornecedor (opcional)')
    lote_qty = ft.TextField(value='1', width=150, hint_text='Quantidade (ex: 10)')
    # Criar DatePicker com fallback:
    # Algumas versões do Flet aceitam `label` no construtor de
    # `DatePicker`, outras não. Para garantir que o formulário funcione
    # em ambientes diferentes (desktop/web/versões antigas), fazemos:
    # 1) Tentar criar `DatePicker(label=...)` — se funcionar, usamos.
    # 2) Se gerar erro, criamos um `Text` como label e um `TextField`
    #    de fallback para que o usuário possa digitar a data no
    #    formato `YYYY-MM-DD`.
    try:
        lote_expiry = ft.DatePicker(label='Data de vencimento', width=220, value=(datetime.today() + timedelta(days=30)).date())
        lote_expiry_label = None
        lote_expiry_field = None
    except Exception:
        # fallback: DatePicker sem label pode existir, mas para ser mais
        # explícitos usamos `lote_expiry=None` e um `TextField` como
        # entrada de data alternativa.
        lote_expiry = None
        lote_expiry_label = ft.Text('Data de vencimento')
        lote_expiry_field = ft.TextField(hint_text='YYYY-MM-DD', width=220)
    add_lote_btn = ft.Button('Adicionar lote')
    # id do lote sendo editado
    editing_batch_id = None

    lote_table = ft.DataTable(columns=[
        ft.DataColumn(ft.Text('ID')),
        ft.DataColumn(ft.Text('Produto')),
        ft.DataColumn(ft.Text('Fornecedor')),
        ft.DataColumn(ft.Text('Quantidade')),
        ft.DataColumn(ft.Text('Vencimento')),
        ft.DataColumn(ft.Text('Ações')),
    ], rows=[])

    def reconstruir_tabela_lotes():
        lote_table.rows.clear()
        for b in db.lotes:
            p = db.produtos.get(b.get('produto_id'))
            s = db.fornecedores.get(b.get('fornecedor_id')) if b.get('fornecedor_id') else None
            fornecedor_nome = s['nome'] if s else '-'
            lote_table.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(str(b['id']))),
                ft.DataCell(ft.Text(p['nome'] if p else '')),
                ft.DataCell(ft.Text(fornecedor_nome)),
                ft.DataCell(ft.Text(str(b.get('quantidade')))),
                ft.DataCell(ft.Text(b.get('vencimento_raw') or '')),
                ft.DataCell(ft.Row([
                    ft.IconButton(ft.icons.Icons.DELETE, tooltip='Remover', on_click=lambda e, bid=b['id']: remover_lote_ui(bid)),
                    ft.IconButton(ft.icons.Icons.EDIT, tooltip='Editar', on_click=lambda e, bid=b['id']: iniciar_edicao_lote(bid))
                ]))
            ]))
        page.update()

    def add_lote(e):
        # add_lote: handler do botão de adicionar/editar lote.
        # Aceita tanto o `DatePicker` (quando disponível) quanto o
        # `TextField` fallback. Constrói a string `expiry_raw` e cria
        # ou atualiza o lote no banco.
        if not lote_product_dropdown.value:
            mostrar_mensagem('Erro', 'Selecione o produto')
            return
        prod = next((p for p in db.produtos.values() if p['nome'] == lote_product_dropdown.value), None)
        sup = next((s for s in db.fornecedores.values() if s['nome'] == lote_supplier_dropdown.value), None) if lote_supplier_dropdown.value else None
        try:
            # aceita DatePicker (objeto date) ou string. Se DatePicker não suportado, usa campo de texto YYYY-MM-DD
            if lote_expiry is not None:
                expiry_val = lote_expiry.value
            else:
                expiry_val = lote_expiry_field.value
            if hasattr(expiry_val, 'strftime'):
                expiry_raw = expiry_val.strftime('%Y-%m-%d')
            else:
                expiry_raw = str(expiry_val)
            nonlocal editing_batch_id
            if editing_batch_id is None:
                db.adicionar_lote(prod['id'], sup['id'] if sup else None, int(lote_qty.value), expiry_raw)
            else:
                db.atualizar_lote(editing_batch_id, prod['id'], sup['id'] if sup else None, int(lote_qty.value), expiry_raw)
                editing_batch_id = None
                add_lote_btn.text = 'Adicionar lote'
                try:
                    add_lote_btn.update()
                except Exception:
                    pass
            reconstruir_tabela_lotes()
        except Exception as ex:
            mostrar_mensagem('Erro', str(ex))

    def remover_lote_ui(bid):
        db.remover_lote(bid)
        reconstruir_tabela_lotes()

    add_lote_btn.on_click = add_lote

    def iniciar_edicao_lote(bid):
        # start_edit_batch: pré-preenche o formulário de lote com os
        # valores do lote selecionado para edição (produto, fornecedor,
        # quantidade e data). Ajusta o botão para salvar alterações.
        nonlocal editing_batch_id
        b = next((x for x in db.lotes if x['id'] == bid), None)
        if not b:
            mostrar_mensagem('Erro', 'Lote não encontrado')
            return
        editing_batch_id = bid
        # preencher campos
        prod = db.produtos.get(b.get('produto_id'))
        lote_product_dropdown.value = prod['nome'] if prod else None
        lote_supplier_dropdown.value = db.fornecedores[b.get('fornecedor_id')]['nome'] if b.get('fornecedor_id') and b.get('fornecedor_id') in db.fornecedores else None
        lote_qty.value = str(b.get('quantidade'))
        try:
            if lote_expiry is not None:
                lote_expiry.value = b.get('vencimento') if b.get('vencimento') else None
            elif lote_expiry_field is not None:
                lote_expiry_field.value = b.get('vencimento_raw') if b.get('vencimento_raw') else ''
        except Exception:
            pass
        add_lote_btn.text = 'Salvar alterações'
        try:
            add_lote_btn.update()
        except Exception:
            pass

    # montar dinamicamente os controles do formulário (incluir label separado quando necessário)
    lote_form_controls = [ft.Text('Adicionar lote'), lote_product_dropdown, lote_supplier_dropdown, lote_qty]
    if lote_expiry_label is not None:
        lote_form_controls.append(lote_expiry_label)
    # anexar o controle disponível: DatePicker ou TextField fallback
    if lote_expiry is not None:
        lote_form_controls.append(lote_expiry)
    elif lote_expiry_field is not None:
        lote_form_controls.append(lote_expiry_field)
    lote_form_controls.append(add_lote_btn)

    lotes_view = ft.Row([
        ft.Column(lote_form_controls, width=420, spacing=10),
        ft.VerticalDivider(width=20),
        ft.Column([ft.Text('Lotes/Estoque atual'), lote_table], expand=1)
    ], expand=True)

    # --------------------- TELA: ENTREGADORES ---------------------
    campo_nome_entregador = ft.TextField(label='Nome entregador', width=300)

    btn_adicionar_entregador = ft.Button('Adicionar entregador')
    # estado de edição para entregadores
    id_entregador_editando = None

    tabela_entregadores = ft.DataTable(columns=[
        ft.DataColumn(ft.Text('ID')),
        ft.DataColumn(ft.Text('Nome')),
        ft.DataColumn(ft.Text('Pendentes')),
        ft.DataColumn(ft.Text('Ações')),
    ], rows=[])

    def reconstruir_tabela_entregadores():
        tabela_entregadores.rows.clear()
        for did, d in db.entregadores.items():
            cnt = db.contar_entregas_para(did)
            tabela_entregadores.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(str(did))),
                ft.DataCell(ft.Text(d['nome'])),
                ft.DataCell(ft.Text(str(cnt))),
                ft.DataCell(ft.Row([
                    ft.IconButton(ft.icons.Icons.DELETE, tooltip='Remover', on_click=lambda e, id=did: remove_deliverer(id)),
                    ft.IconButton(ft.icons.Icons.EDIT, tooltip='Editar', on_click=lambda e, id=did: start_edit_deliverer(id))
                ]))
            ]))
        # atualizar dropdown do caixa
        dropdown_entregador.options = [ft.dropdown.Option(d['nome']) for d in db.entregadores.values()]
        page.update()

    def adicionar_entregador(e):
        # adicionar_entregador: se não estivermos em modo de edição cria um
        # novo entregador; se estivermos, atualiza o entregador em edição.
        try:
            nonlocal id_entregador_editando
            name = campo_nome_entregador.value.strip()
            if not name:
                mostrar_mensagem('Erro', 'Preencha o nome do entregador')
                return
            if id_entregador_editando is None:
                db.adicionar_entregador(name)
            else:
                db.atualizar_entregador(id_entregador_editando, name)
                id_entregador_editando = None
                btn_adicionar_entregador.text = 'Adicionar entregador'
                try:
                    btn_adicionar_entregador.update()
                except Exception:
                    pass
            campo_nome_entregador.value = ''
            reconstruir_tabela_entregadores()
        except Exception as ex:
            mostrar_mensagem('Erro', str(ex))

    btn_adicionar_entregador.on_click = adicionar_entregador

    def remove_deliverer(did):
        if did in db.entregadores:
            del db.entregadores[did]
        # cancelar edição se estava editando este entregador
        try:
            nonlocal id_entregador_editando
            if id_entregador_editando == did:
                id_entregador_editando = None
                btn_adicionar_entregador.text = 'Adicionar entregador'
                try:
                    btn_adicionar_entregador.update()
                except Exception:
                    pass
        except Exception:
            pass
        reconstruir_tabela_entregadores()

    def start_edit_deliverer(did):
        nonlocal id_entregador_editando
        d = db.entregadores.get(did)
        if not d:
            mostrar_mensagem('Erro', 'Entregador não encontrado')
            return
        id_entregador_editando = did
        campo_nome_entregador.value = d['nome']
        btn_adicionar_entregador.text = 'Salvar alterações'
        try:
            btn_adicionar_entregador.update()
        except Exception:
            pass

    deliverers_view = ft.Row([
        ft.Column([ft.Text('Entregadores'), tabela_entregadores], expand=1),
        ft.VerticalDivider(width=20),
        ft.Column([ft.Text('Adicionar entregador'), campo_nome_entregador, btn_adicionar_entregador], width=420)
    ], expand=True)

    # --------------------- TELA: RELATÓRIOS ---------------------
    expired_table = ft.DataTable(columns=[
        ft.DataColumn(ft.Text('Lote ID')),
        ft.DataColumn(ft.Text('Produto')),
        ft.DataColumn(ft.Text('Quantidade')),
        ft.DataColumn(ft.Text('Vencimento')),
    ], rows=[])

    near_table = ft.DataTable(columns=[
        ft.DataColumn(ft.Text('Lote ID')),
        ft.DataColumn(ft.Text('Produto')),
        ft.DataColumn(ft.Text('Quantidade')),
        ft.DataColumn(ft.Text('Vence em (dias)')),
        ft.DataColumn(ft.Text('Desconto (%)')),
    ], rows=[])

    def reconstruir_relatorios():
        expired_table.rows.clear()
        for b in db.produtos_vencidos():
            p = db.produtos.get(b.get('produto_id'))
            expired_table.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(str(b['id']))),
                ft.DataCell(ft.Text(p['nome'] if p else '')),
                ft.DataCell(ft.Text(str(b.get('quantidade')))),
                ft.DataCell(ft.Text(b.get('vencimento_raw') or '')),
            ]))
        near_table.rows.clear()
        for b in db.produtos_perto_vencimento():
            p = db.produtos.get(b.get('produto_id'))
            days_left = (b.get('vencimento') - datetime.today().date()).days if b.get('vencimento') else '-'
            discount = p.get('desconto_perto_vencimento', 0) if p else 0
            near_table.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(str(b['id']))),
                ft.DataCell(ft.Text(p['nome'] if p else '')),
                ft.DataCell(ft.Text(str(b.get('quantidade')))),
                ft.DataCell(ft.Text(str(days_left))),
                ft.DataCell(ft.Text(str(discount))),
            ]))
        page.update()

    reports_view = ft.Column([
        ft.Text('Relatórios diários'),
        ft.Row([ft.Button('Atualizar relatório', on_click=lambda e: reconstruir_relatorios())]),
        ft.Text('Produtos vencidos:'), expired_table,
        ft.Divider(),
        ft.Text('Produtos perto de vencer (desconto automático):'), near_table
    ], expand=1)

    # --------------------- BARRA SUPERIOR (visível em todas as telas) ---------------------
    def set_main_view(view):
        # Mantém a barra superior e o banner; substitui sempre a área de conteúdo (índice 2)
        if page.controls:
            stack = page.controls[0]
            # se o stack já tem uma coluna principal, substitui seus controles
            if stack.controls:
                main_col = stack.controls[0]
                main_col.controls = [top_bar, sale_msg_row, view]
            else:
                stack.controls.append(ft.Column([top_bar, sale_msg_row, view], expand=True))
        else:
            # adiciona o stack com a coluna principal
            main_stack.controls.append(ft.Column([top_bar, sale_msg_row, view], expand=True))
            page.add(main_stack)
        page.update()

    def mudar_tela(screen):
        state['current_screen'] = screen
        # rebuilds e atualizações quando necessário
        if screen == 'caixa':
            set_main_view(caixa_view)
        elif screen == 'produtos':
            reconstruir_lista_produtos()
            set_main_view(products_view)
        elif screen == 'fornecedores':
            reconstruir_lista_fornecedores()
            set_main_view(suppliers_view)
        elif screen == 'lotes':
            reconstruir_tabela_lotes()
            set_main_view(lotes_view)
        elif screen == 'entregadores':
            reconstruir_tabela_entregadores()
            set_main_view(deliverers_view)
        elif screen == 'relatorios':
            reconstruir_relatorios()
            set_main_view(reports_view)

    top_bar = ft.Row([
        ft.Button('Caixa', on_click=lambda e: mudar_tela('caixa')),
        ft.Button('Produtos', on_click=lambda e: mudar_tela('produtos')),
        ft.Button('Fornecedores', on_click=lambda e: mudar_tela('fornecedores')),
        ft.Button('Lotes/Estoque', on_click=lambda e: mudar_tela('lotes')),
        ft.Button('Entregadores', on_click=lambda e: mudar_tela('entregadores')),
        ft.Button('Relatórios', on_click=lambda e: mudar_tela('relatorios')),
    ], alignment=ft.MainAxisAlignment.SPACE_EVENLY)

    # Monta página: top_bar + banner + view atual dentro do main_stack (para overlay funcionar)
    main_stack.controls.append(ft.Column([top_bar, sale_msg_row, caixa_view], expand=True))
    page.add(main_stack)

    # Inicializar listas
    reconstruir_lista_produtos()
    reconstruir_lista_fornecedores()
    reconstruir_tabela_lotes()
    reconstruir_tabela_entregadores()
    reconstruir_relatorios()


if __name__ == '__main__':
    ft.run(main)