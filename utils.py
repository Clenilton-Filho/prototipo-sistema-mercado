"""Funções utilitárias pequenas usadas pela UI.

Atualmente contém formatação de moeda usada nas views para exibir preços.
"""


def formatar_moeda(v):
    """Formata número como moeda brasileira (ex.: R$ 1.234,56)."""
    return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')


# alias para compatibilidade com chamadas antigas
format_currency = formatar_moeda
