"""Ponto de entrada da aplicação.

Este arquivo inicia a aplicação Flet chamando `main` em `views.app`.
"""

import flet as ft
from views.app import main

# Executar localmente com: `python main.py`
if __name__ == '__main__':
    ft.run(main)
