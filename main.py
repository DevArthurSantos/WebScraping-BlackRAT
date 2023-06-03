from WebScraping import WebScraping

ws = WebScraping()
ws.init_driver('Dinheiro')
ws.login('Thiagosilvaf37@gmail.com', 'mestoz-zytba7-Kuggym')
ws.pesquisar("Dinheiro")
ws.fechar_navegador()