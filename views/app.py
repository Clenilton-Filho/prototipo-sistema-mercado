import flet as ft
from datetime import datetime, timedelta

from banco_memoria import BancoMemoria
from views.overlay import OverlayManager
from views.caixa import CaixaView
from views.produtos import ProdutosView
from views.fornecedores import FornecedoresView
from views.lotes import LotesView
from views.entregadores import EntregadoresView
from views.relatorios import RelatoriosView

# Para executar: `python main.py` (assume que o pacote `flet` está instalado).
# Se você nunca viu Flet: a função `main(page)` é o ponto de entrada. O
# objeto `page` representa a janela e você adiciona `controls` (widgets)
# a ele. Elementos como `ft.Column`, `ft.Row`, `ft.Button` e `ft.Text`
# compõem a interface. Muitas funções abaixo criam/atualizam controles e
# chamam `page.update()` para refletir mudanças na tela.

# Sistema simples em memória para um mercado (uso interno por funcionários)
# Arquitetura: um único arquivo para facilitar entendimento de iniciantes.
# Banco de dados em memória: dicionários e listas.


def main(page: ft.Page):
    # Configurações iniciais da página
    page.title = 'Projeto Mercado - Caixa'
    page.theme_mode = 'light'  # tema claro
    page.window_maximized = True

    # `page` é a janela principal da aplicação. Aqui configuramos título,
    # tema e estado inicial da janela. A partir daqui criamos os controles
    # (widgets) e funções que reagem a eventos (cliques, mudanças de valor).

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

    # Observação sobre mensagens: durante desenvolvimento usamos `print`
    # para debug; antes de entregar/remover estes prints, substitua por
    # logs ou remova para não poluir o console do usuário.

    caixa = CaixaView(page, db, overlay, state)
    produtos = ProdutosView(page, db, overlay, caixa.product_dropdown)
    fornecedores = FornecedoresView(page, db, overlay)
    lotes = LotesView(page, db, overlay)
    entregadores = EntregadoresView(page, db, overlay, caixa.dropdown_entregador)
    relatorios = RelatoriosView(page, db, overlay)

    # Wire cross-view dependencies
    caixa.reconstruir_entregadores_callback = entregadores.reconstruir

    # --------------------- BARRA SUPERIOR (visível em todas as telas) ---------------------
    def set_main_view(view):
        # Mantém a barra superior e o banner; substitui sempre a área de conteúdo (índice 2)
        if page.controls:
            stack = page.controls[0]
            # se o stack já tem uma coluna principal, substitui seus controles
            if stack.controls:
                main_col = stack.controls[0]
                main_col.controls = [top_bar, caixa.sale_msg_row, view]
            else:
                stack.controls.append(ft.Column([top_bar, caixa.sale_msg_row, view], expand=True))
        else:
            # adiciona o stack com a coluna principal
            main_stack.controls.append(ft.Column([top_bar, caixa.sale_msg_row, view], expand=True))
            page.add(main_stack)
        page.update()

    def mudar_tela(screen):
        state['current_screen'] = screen
        # rebuilds e atualizações quando necessário
        if screen == 'caixa':
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
    main_stack.controls.append(ft.Column([top_bar, caixa.sale_msg_row, caixa.view], expand=True))
    page.add(main_stack)

    # Inicializar listas
    produtos.reconstruir()
    fornecedores.reconstruir()
    lotes.reconstruir()
    entregadores.reconstruir()
    relatorios.reconstruir()
