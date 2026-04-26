def formatar_moeda(v):
    return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# alias para compatibilidade com chamadas antigas
format_currency = formatar_moeda
