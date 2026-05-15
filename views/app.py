import flet as ft
from datetime import datetime, timedelta

from banco_SQLITE import BancoMemoria
from views.overlay import OverlayManager
from views.caixa import CaixaView
from views.produtos import ProdutosView
from views.fornecedores import FornecedoresView
from views.lotes import LotesView
from views.entregadores import EntregadoresView
from views.relatorios import RelatoriosView
from views.auth import mostrar_auth_overlay

# Para executar: `python main.py` (assume que o pacote `flet` está instalado).
# Se você nunca viu Flet: a função `main(page)` é o ponto de entrada. O
# objeto `page` representa a janela e você adiciona `controls` (widgets)
# a ele. Elementos como `ft.Column`, `ft.Row`, `ft.Button` e `ft.Text`
# compõem a interface. Muitas funções abaixo criam/atualizam controles e
# chamam `page.update()` para refletir mudanças na tela.

# Observações sobre persistência e arquitetura
# - O projeto usa `BancoMemoria`, que fornece uma camada de persistência
#   baseada em SQLite (arquivo `data/mercado.db`). O nome da classe foi
#   mantido por compatibilidade com versões anteriores do código.
# - A UI é organizada em várias "views" (módulos em `views/`) para
#   manter responsabilidades separadas: `Caixa`, `Produtos`, `Lotes`, etc.


def main(page: ft.Page):
    # Configurações iniciais da página
    page.title = 'Projeto Mercado - Caixa'
    page.theme_mode = 'light'  # tema claro
    page.window_maximized = True

    # `page` é a janela principal da aplicação. Aqui configuramos título,
    # tema e estado inicial da janela. A partir daqui criamos os controles
    # (widgets) e funções que reagem a eventos (cliques, mudanças de valor).

    db = BancoMemoria()

    # Preencher com alguns dados de exemplo para o relatório padrão (somente se não existirem)
    try:
        if not any(p['codigo'] == 'ARZ5' or p['nome'] == 'Arroz 5kg' for p in db.produtos.values()):
            pid1 = db.adicionar_produto('Arroz 5kg', 'ARZ5', 25.0, discount_near_expiry=20.0, near_days=5)
        else:
            pid1 = next((p['id'] for p in db.produtos.values() if p['codigo'] == 'ARZ5' or p['nome'] == 'Arroz 5kg'), None)
        if not any(p['codigo'] == 'FJ1' or p['nome'] == 'Feijão 1kg' for p in db.produtos.values()):
            pid2 = db.adicionar_produto('Feijão 1kg', 'FJ1', 8.0, discount_near_expiry=10.0, near_days=7)
        else:
            pid2 = next((p['id'] for p in db.produtos.values() if p['codigo'] == 'FJ1' or p['nome'] == 'Feijão 1kg'), None)
    except Exception:
        # se algum erro ocorrer ao seed (por exemplo, concorrência), tentamos recuperar IDs existentes
        pid1 = next((p['id'] for p in db.produtos.values() if p['codigo'] == 'ARZ5' or p['nome'] == 'Arroz 5kg'), None)
        pid2 = next((p['id'] for p in db.produtos.values() if p['codigo'] == 'FJ1' or p['nome'] == 'Feijão 1kg'), None)
    try:
        if not any(s['nome'] == 'Fornecedor A' for s in db.fornecedores.values()):
            sid1 = db.adicionar_fornecedor('Fornecedor A')
        else:
            sid1 = next((s['id'] for s in db.fornecedores.values() if s['nome'] == 'Fornecedor A'), None)
    except Exception:
        sid1 = next((s['id'] for s in db.fornecedores.values() if s['nome'] == 'Fornecedor A'), None)
    try:
        if pid1 and sid1:
            db.fornecedor_definir_preco(sid1, pid1, 23.0)
        if pid2 and sid1:
            db.fornecedor_definir_preco(sid1, pid2, 7.5)
        # adicionar lotes de exemplo apenas se não existirem para o produto
        try:
            existing_batches = db.lotes
        except Exception:
            existing_batches = []
        if pid1 and sid1:
            if not any(b['produto_id'] == pid1 for b in existing_batches):
                db.adicionar_lote(pid1, sid1, 10, (datetime.today() + timedelta(days=2)).strftime('%Y-%m-%d'))
        if pid2 and sid1:
            if not any(b['produto_id'] == pid2 for b in existing_batches):
                db.adicionar_lote(pid2, sid1, 5, (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d'))
    except Exception:
        pass
    try:
        if not any(d['nome'] == 'Entregador 1' for d in db.entregadores.values()):
            did1 = db.adicionar_entregador('Entregador 1')
        else:
            did1 = next((d['id'] for d in db.entregadores.values() if d['nome'] == 'Entregador 1'), None)
    except Exception:
        did1 = next((d['id'] for d in db.entregadores.values() if d['nome'] == 'Entregador 1'), None)

    # Estado da aplicação
    state = {
        'current_screen': 'caixa',
        'cart': [],  # itens: {product_id, qty, unit_price, name}
        'delivery_enabled': False,
        'selected_deliverer': None,
    }

    # Funções utilitárias UI
    def atualizar_top_bar():
        # nada dinâmico aqui por enquanto
        pass

    main_stack = ft.Stack(expand=True)
    overlay = OverlayManager(page, main_stack)
    caixa = CaixaView(page, db, overlay, state)
    produtos = ProdutosView(page, db, overlay, caixa.product_dropdown, product_refresh_cb=caixa.atualizar_product_options)
    fornecedores = FornecedoresView(page, db, overlay)
    lotes = LotesView(page, db, overlay, product_refresh_cb=caixa.atualizar_product_options)
    entregadores = EntregadoresView(page, db, overlay, caixa.dropdown_entregador)
    relatorios = RelatoriosView(page, db, overlay)

    caixa.reconstruir_entregadores_callback = entregadores.reconstruir

    # --------------------- BARRA SUPERIOR (visível em todas as telas) ---------------------
    def set_main_view(view):
        # Mantém a barra superior e o banner; substitui sempre a área de conteúdo (índice 2)
        if page.controls:
            stack = page.controls[0]
            # se o stack já tem uma coluna principal, substitui seus controles
            if stack.controls:
                main_col = stack.controls[0]
                # adicionar espaçamento entre a barra superior e o conteúdo
                main_col.controls = [top_bar, ft.Container(height=12), caixa.sale_msg_row, view]
            else:
                stack.controls.append(ft.Column([top_bar, ft.Container(height=12), caixa.sale_msg_row, view], expand=True))
        else:
            # adiciona o stack com a coluna principal
            main_stack.controls.append(ft.Column([top_bar, ft.Container(height=12), caixa.sale_msg_row, view], expand=True))
            page.add(main_stack)
        page.update()

    def mudar_tela(screen):
        state['current_screen'] = screen
        # rebuilds e atualizações quando necessário
        if screen == 'caixa':
            caixa.reconstruir()
            set_main_view(caixa.view)
        elif screen == 'produtos':
            produtos.reconstruir()
            set_main_view(produtos.view)
        elif screen == 'fornecedores':
            fornecedores.reconstruir()
            set_main_view(fornecedores.view)
        elif screen == 'lotes':
            lotes.reconstruir()
            set_main_view(lotes.view)
        elif screen == 'entregadores':
            entregadores.reconstruir()
            set_main_view(entregadores.view)
        elif screen == 'relatorios':
            relatorios.reconstruir()
            set_main_view(relatorios.view)

    top_bar = ft.Row([
        ft.Button('Caixa', on_click=lambda e: mudar_tela('caixa')),
        ft.Button('Produtos', on_click=lambda e: mudar_tela('produtos')),
        ft.Button('Fornecedores', on_click=lambda e: mudar_tela('fornecedores')),
        ft.Button('Lotes/Estoque', on_click=lambda e: mudar_tela('lotes')),
        ft.Button('Entregadores', on_click=lambda e: mudar_tela('entregadores')),
        ft.Button('Relatórios', on_click=lambda e: mudar_tela('relatorios')),
    ], alignment=ft.MainAxisAlignment.SPACE_EVENLY)

    # Monta página: top_bar + banner + view atual dentro do main_stack (para overlay funcionar)
    main_stack.controls.append(ft.Column([top_bar, ft.Container(height=12), caixa.sale_msg_row, caixa.view], expand=True))
    page.add(main_stack)

    # mostrar modal de autenticação ao iniciar (bloqueia acesso até logar)
    def _on_auth_success():
        try:
            overlay.mostrar_mensagem('Bem-vindo', 'Acesso concedido')
        except Exception:
            pass
    try:
        mostrar_auth_overlay(overlay, db, on_success=_on_auth_success)
    except Exception:
        pass

    # Inicializar listas (após criação da UI principal)
    produtos.reconstruir()
    fornecedores.reconstruir()
    lotes.reconstruir()
    entregadores.reconstruir()
    relatorios.reconstruir()
    # garantir que caixa tenha opções atualizadas ao iniciar
    try:
        caixa.reconstruir()
    except Exception:
        pass
