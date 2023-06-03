from WebScraping import WebScraping

# Inicialize a instância da classe WebScraping
ws = WebScraping()

# Inicialize o driver e defina o diretório de destino
folder_path = 'Dinheiro'
ws.init_driver(folder_path)

# Faça o login
success = ws.login('Thiagosilvaf37@gmail.com', 'mestoz-zytba7-Kuggym')

if success:
    print('Login realizado com sucesso!')
    # Realize as operações de scraping desejadas
    ws.pesquisar("Dinheiro")
else:
    print('Falha no login. Verifique as credenciais fornecidas.')

# Feche o navegador
ws.fechar_navegador()
