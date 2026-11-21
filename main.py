
from playwright.sync_api import sync_playwright

print("Iniciando automação...")

with sync_playwright() as p:

    print("Abrindo Chromium...")

    navegador = p.chromium.launch(
        headless=False
    )

    print("Navegador iniciado!")

    pagina = navegador.new_page()

    pagina.goto("https://www.google.com")

    print("Página acessada!")
    print("Título:", pagina.title())

    input("Pressione ENTER para fechar o navegador...")

    navegador.close()
