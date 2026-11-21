
from playwright.sync_api import sync_playwright, expect

def executar_robo():

    navegador = None

    print("===================================")
    print("       WEBFLOW AUTOMATION")
    print("       ROBÔ DE LOGIN WEB")
    print("===================================")

    try:
        with sync_playwright() as p:

            # 1. Iniciar navegador
            navegador = p.chromium.launch(
                headless=False
            )

            # 2. Criar uma nova página
            pagina = navegador.new_page()

            print("\n[1] Acessando sistema...")

            pagina.goto(
                "https://the-internet.herokuapp.com/login"
            )

            print("[2] Preenchendo usuário...")

            pagina.get_by_label("Username").fill("tomsmith")

            print("[3] Preenchendo senha...")

            pagina.get_by_label("Password").fill(
                "SuperSecretPassword!"
            )

            print("[4] Realizando login...")

            pagina.get_by_role(
                "button",
                name="Login"
            ).click()

            print("[5] Verificando resultado...")

            # 3. Validar login
            expect(
                pagina.locator("#flash")
            ).to_contain_text(
                "You logged into a secure area!"
            )

            print("\n===================================")
            print("       LOGIN REALIZADO!")
            print("       AUTOMACAO CONCLUIDA")
            print("===================================")

    except Exception as erro:

        print("\nERRO NA AUTOMACAO!")
        print(f"Detalhes: {erro}")

        raise

    finally:

        # 4. Encerramento automático
        if navegador and navegador.is_connected():
            navegador.close()

        print("\nNavegador encerrado.")
        print("WebFlow Automation finalizada.")


if __name__ == "__main__":
    executar_robo()
