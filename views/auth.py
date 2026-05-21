import flet as ft


def mostrar_auth_overlay(overlay, db, on_success=None):
        
    """
    Ponto de entrada para mostrar os modais de autenticação (login / registro).

    Explicação curta para iniciantes:
    - Este módulo cria dois modais separados: o de `Login` aparece primeiro.
    - O botão "Registrar" abre o modal de registro que substitui o de login.
    - O modal só é fechado quando o usuário efetua login com sucesso.
    - O parâmetro `overlay` é uma instância de `OverlayManager` já presente
        no projeto; usamos `mostrar_overlay` para exibir os diálogos.

    Parâmetros:
    - overlay: gerenciador de overlay da UI (veja `views/overlay.py`)
    - db: instância de `BancoMemoria` usada para gravar/validar usuários
    - on_success: callback opcional chamado quando o login é bem sucedido
    """
    # Funções auxiliares de validação
    def has_letter(s):
        return any(c.isalpha() for c in s)

    def has_digit(s):
        return any(c.isdigit() for c in s)

    def has_upper(s):
        return any(c.isupper() for c in s)

    def has_special(s):
        return any(not c.isalnum() for c in s)
    # LOGIN modal
    def show_login(message: str = None):
        login_user = ft.TextField(label='Usuário', width=260)
        login_pass = ft.TextField(label='Senha', password=True, can_reveal_password=True, width=260)

        msg_text = ft.Text(message or '', color=ft.Colors.GREEN) if message else ft.Text('')
        def do_login(e=None):
            u = (login_user.value or '').strip()
            p = login_pass.value or ''
            if not u or not p:
                # mostrar aviso com botão fechar que reabre o login
                overlay.mostrar_overlay('Erro', ft.Text('Preencha usuário e senha'), on_close=lambda: show_login(), show_close_button=True)
                return
            ok = db.autenticar_usuario(u, p)
            if not ok:
                overlay.mostrar_overlay('Erro', ft.Text('Usuário ou senha inválidos'), on_close=lambda: show_login(), show_close_button=True)
                return
            # sucesso
            overlay.fechar_overlay()
            if on_success:
                try:
                    on_success()
                except Exception:
                    pass

        btn_login = ft.Button('Entrar', on_click=do_login)
        # permitir Enter nos campos para submeter o login
        login_user.on_submit = do_login
        login_pass.on_submit = do_login

        def abrir_registro(e=None):
            show_register()

        btn_to_register = ft.TextButton('Registrar', on_click=abrir_registro)

        # reduzir largura do conteúdo para evitar espaço vazio à direita
        buttons_row = ft.Row([btn_login, btn_to_register], alignment=ft.MainAxisAlignment.CENTER)
        col = ft.Column([ft.Text('Login', weight=ft.FontWeight.BOLD), login_user, login_pass, msg_text, buttons_row], tight=True, width=340, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        overlay.mostrar_overlay('Login', col, show_close_button=False, card_width=380)

    # REGISTER modal
    def show_register():
        reg_user = ft.TextField(label='Novo usuário', width=260)
        reg_pass = ft.TextField(label='Senha', password=True, can_reveal_password=True, width=260)
        reg_pass2 = ft.TextField(label='Repita a senha', password=True, can_reveal_password=True, width=260)
        reg_estab = ft.TextField(label='Senha do estabelecimento', password=True, can_reveal_password=True, width=260)

        # requisitos visuais
        req_user_len = ft.Row([ft.Icon(ft.icons.Icons.CHECK, color=ft.Colors.GREEN) if False else ft.Icon(ft.icons.Icons.CLOSE, color=ft.Colors.RED), ft.Text('Usuário >= 4 caracteres')])

        req_pass_len = ft.Row([ft.Icon(ft.icons.Icons.CHECK, color=ft.Colors.GREEN) if False else ft.Icon(ft.icons.Icons.CLOSE, color=ft.Colors.RED), ft.Text('Senha >= 8 caracteres')])
        req_pass_digit = ft.Row([ft.Icon(ft.icons.Icons.CHECK, color=ft.Colors.GREEN) if False else ft.Icon(ft.icons.Icons.CLOSE, color=ft.Colors.RED), ft.Text('Contém números')])
        req_pass_upper = ft.Row([ft.Icon(ft.icons.Icons.CHECK, color=ft.Colors.GREEN) if False else ft.Icon(ft.icons.Icons.CLOSE, color=ft.Colors.RED), ft.Text('Contém letras maiúsculas')])
        req_pass_special = ft.Row([ft.Icon(ft.icons.Icons.CHECK, color=ft.Colors.GREEN) if False else ft.Icon(ft.icons.Icons.CLOSE, color=ft.Colors.RED), ft.Text('Contém caractere especial')])

        def update_reqs(e=None):
            u = (reg_user.value or '')
            p = (reg_pass.value or '')
            # username
            ok_len = len(u) >= 4
            req_user_len.controls[0] = ft.Icon(ft.icons.Icons.CHECK, color=ft.Colors.GREEN) if ok_len else ft.Icon(ft.icons.Icons.CLOSE, color=ft.Colors.RED)
            # password
            ok_plen = len(p) >= 8
            ok_pdigit = has_digit(p)
            ok_pupper = has_upper(p)
            ok_pspecial = has_special(p)
            req_pass_len.controls[0] = ft.Icon(ft.icons.Icons.CHECK, color=ft.Colors.GREEN) if ok_plen else ft.Icon(ft.icons.Icons.CLOSE, color=ft.Colors.RED)
            req_pass_digit.controls[0] = ft.Icon(ft.icons.Icons.CHECK, color=ft.Colors.GREEN) if ok_pdigit else ft.Icon(ft.icons.Icons.CLOSE, color=ft.Colors.RED)
            req_pass_upper.controls[0] = ft.Icon(ft.icons.Icons.CHECK, color=ft.Colors.GREEN) if ok_pupper else ft.Icon(ft.icons.Icons.CLOSE, color=ft.Colors.RED)
            req_pass_special.controls[0] = ft.Icon(ft.icons.Icons.CHECK, color=ft.Colors.GREEN) if ok_pspecial else ft.Icon(ft.icons.Icons.CLOSE, color=ft.Colors.RED)
            try:
                req_user_len.update(); req_pass_len.update(); req_pass_digit.update(); req_pass_upper.update(); req_pass_special.update()
            except Exception:
                pass

        reg_user.on_change = update_reqs
        reg_pass.on_change = update_reqs
        reg_pass2.on_change = update_reqs

        def do_register(e=None):
            u = (reg_user.value or '').strip()
            p1 = reg_pass.value or ''
            p2 = reg_pass2.value or ''
            estab = reg_estab.value or ''
            # checar unicidade primeiro para dar mensagem específica
            if db.usuario_existe(u):
                overlay.mostrar_overlay('Erro', ft.Text('Usuário já existe'), on_close=lambda: show_register(), show_close_button=True)
                return
            # validações
            if not db.verificar_senha_estabelecimento(estab):
                overlay.mostrar_overlay('Erro', ft.Text('Senha do estabelecimento inválida'), on_close=lambda: show_register(), show_close_button=True)
                return
            if len(u) < 4:
                overlay.mostrar_overlay('Erro', ft.Text('Usuário deve ter ao menos 4 caracteres'), on_close=lambda: show_register(), show_close_button=True)
                return
            if p1 != p2:
                overlay.mostrar_overlay('Erro', ft.Text('Senhas não coincidem'), on_close=lambda: show_register(), show_close_button=True)
                return
            # senha: comprimento, dígito, maiúscula e caractere especial
            ok_len_p = len(p1) >= 8
            ok_digit_p = has_digit(p1)
            ok_upper_p = has_upper(p1)
            ok_special_p = has_special(p1)
            if not (ok_len_p and ok_digit_p and ok_upper_p and ok_special_p):
                overlay.mostrar_overlay('Erro', ft.Text('Senha não atende os requisitos'), on_close=lambda: show_register(), show_close_button=True)
                return
            try:
                db.adicionar_usuario(u, p1)
            except Exception as ex:
                overlay.mostrar_overlay('Erro', ft.Text(str(ex)), on_close=lambda: show_register(), show_close_button=True)
                return
            # registro ok -> voltar para login
            show_login('Registrado com sucesso. Faça login.')

        btn_reg = ft.Button('Registrar', on_click=do_register)
        btn_cancel = ft.TextButton('Voltar ao login', on_click=lambda e: show_login())

        # permitir Enter no formulário de registro para submeter
        reg_user.on_submit = do_register
        reg_pass.on_submit = do_register
        reg_pass2.on_submit = do_register
        reg_estab.on_submit = do_register

        left_col = ft.Column([ft.Text('Registrar', weight=ft.FontWeight.BOLD), reg_user, reg_pass, reg_pass2, reg_estab, ft.Row([btn_reg, btn_cancel])], tight=True)
        right_col = ft.Column([ft.Text('Requisitos', weight=ft.FontWeight.BOLD), req_user_len, ft.Divider(), req_pass_len, req_pass_digit, req_pass_upper, req_pass_special], tight=True)

        # ligar updates iniciais
        update_reqs()

        overlay.mostrar_overlay('Registrar usuário', ft.Row([left_col, ft.VerticalDivider(width=20), right_col], alignment=ft.MainAxisAlignment.CENTER), show_close_button=False)

    # mostrar login por padrão
    show_login()

