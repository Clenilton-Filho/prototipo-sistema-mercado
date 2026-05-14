import flet as ft


class OverlayManager:
    # Overlay modal customizado (fallback caso AlertDialog não apareça)
    # Variáveis usadas para o overlay (janela modal que fica sobre a UI).
    # Mantemos `overlay_box` para poder remover/fechar o modal depois.

    def __init__(self, page, main_stack):
        self.page = page
        self.main_stack = main_stack
        self.overlay_box = None
        self.overlay_mode = None

    def fechar_overlay(self, e=None):
        try:
            if self.overlay_box:
                if self.overlay_mode == 'positioned':
                    if self.overlay_box in self.main_stack.controls:
                        self.main_stack.controls.remove(self.overlay_box)
                elif self.overlay_mode == 'page_overlay':
                    try:
                        if hasattr(self.page, 'overlay') and self.overlay_box in self.page.overlay:
                            self.page.overlay.remove(self.overlay_box)
                    except Exception:
                        pass
                else:
                    # fallback: remove from main_stack if present
                    if self.overlay_box in self.main_stack.controls:
                        self.main_stack.controls.remove(self.overlay_box)
            self.overlay_box = None
            self.overlay_mode = None
            self.page.update()
        except Exception:
            pass

        def mostrar_overlay(self, title, content_control, on_close=None, show_close_button=True, card_width=560):
                """
                Exibe um modal (overlay) centralizado sobre a aplicação.

                Parâmetros principais:
                - title: título do modal
                - content_control: controle Flet (ft.Control) que será exibido dentro do card
                - on_close: callback opcional executado quando o modal for fechado
                - show_close_button: se False, o botão 'Fechar' no card não aparece
                    (útil para modais que só devem fechar por ação do usuário, ex.: login)
                - card_width: largura do card branco central (padrão 560), pode ser
                    reduzido para modais mais compactos
                """
        # remove overlay anterior se existir
        self.fechar_overlay()

        # botão de fechar que chama um callback opcional além de fechar o overlay
        def _on_close(e=None):
            try:
                self.fechar_overlay()
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
                (ft.Row([ft.Button('Fechar', on_click=_on_close)], alignment=ft.MainAxisAlignment.END) if show_close_button else ft.Container())
            ], tight=True),
            width=card_width,
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
                self.overlay_box = ft.Positioned(left=0, top=0, right=0, bottom=0, child=overlay_full)
                self.overlay_mode = 'positioned'
                self.main_stack.controls.append(self.overlay_box)
            elif hasattr(self.page, 'overlay'):
                # usar API page.overlay quando disponível
                self.overlay_box = overlay_full
                self.overlay_mode = 'page_overlay'
                self.page.overlay.append(self.overlay_box)
            else:
                # fallback simples: anexar container ao main_stack
                self.overlay_box = overlay_full
                self.overlay_mode = 'stack_fallback'
                self.main_stack.controls.append(self.overlay_box)
        except Exception:
            # último recurso: anexar ao main_stack
            self.overlay_box = overlay_full
            self.overlay_mode = 'stack_fallback'
            try:
                self.main_stack.controls.append(self.overlay_box)
            except Exception:
                pass

        self.page.update()

    def mostrar_mensagem(self, title, content):
        # usa overlay customizado para garantir visibilidade no ambiente do usuário
        try:
            print(f"DEBUG mostrar_mensagem called: {title} | {content}")
            self.mostrar_overlay(title, ft.Text(content))
            print('DEBUG mostrar_mensagem: overlay appended')
        except Exception as ex:
            print('DEBUG mostrar_mensagem failed:', ex)
