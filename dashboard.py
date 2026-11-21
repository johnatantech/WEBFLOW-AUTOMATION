
import tkinter as tk
from datetime import datetime
from threading import Thread, Event
from queue import Queue, Empty
from playwright.sync_api import sync_playwright


# ==========================================
# CONFIGURACOES
# ==========================================

FUNDO = "#111827"
PAINEL = "#1F2937"
AZUL = "#2563EB"
BRANCO = "#FFFFFF"
CINZA = "#9CA3AF"
VERDE = "#22C55E"
VERMELHO = "#EF4444"

DELAY = 1500

fila = Queue()
cancelar_evento = Event()

executando = False
total_execucoes = 0


# ==========================================
# JANELA PRINCIPAL
# ==========================================

janela = tk.Tk()
janela.title("WebFlow Automation")
janela.geometry("1000x680")
janela.configure(bg=FUNDO)
janela.minsize(850, 550)


# ==========================================
# FUNCOES AUXILIARES
# ==========================================

def registrar_log(mensagem):

    horario = datetime.now().strftime("%H:%M:%S")

    logs.insert(
        tk.END,
        f"[{horario}] {mensagem}\n"
    )

    logs.see(tk.END)


def atualizar_status(mensagem, cor=VERDE):

    status.config(
        text=f"● {mensagem}",
        fg=cor
    )


def aguardar(pagina):

    # Espera interrompível pelo usuário
    if cancelar_evento.wait(DELAY / 1000):
        raise InterruptedError(
            "Automacao cancelada pelo usuario."
        )


def verificar_cancelamento():

    if cancelar_evento.is_set():
        raise InterruptedError(
            "Automacao cancelada pelo usuario."
        )


# ==========================================
# AUTOMACAO COM PLAYWRIGHT
# ==========================================

def executar_robo():

    navegador = None
    sucesso = False
    cancelado = False

    try:

        fila.put(("log", "Iniciando Playwright..."))

        with sync_playwright() as p:

            try:

                verificar_cancelamento()

                navegador = p.chromium.launch(
                    headless=False
                )

                pagina = navegador.new_page()

                pagina.set_default_timeout(10000)

                fila.put((
                    "log",
                    "Navegador iniciado."
                ))

                aguardar(pagina)

                verificar_cancelamento()

                fila.put((
                    "log",
                    "Acessando sistema web..."
                ))

                pagina.goto(
                    "https://the-internet.herokuapp.com/login",
                    wait_until="domcontentloaded",
                    timeout=20000
                )

                verificar_cancelamento()
                aguardar(pagina)

                fila.put((
                    "log",
                    "Preenchendo usuario..."
                ))

                pagina.get_by_label("Username").fill(
                    "tomsmith"
                )

                verificar_cancelamento()
                aguardar(pagina)

                fila.put((
                    "log",
                    "Preenchendo senha..."
                ))

                pagina.get_by_label("Password").fill(
                    "SuperSecretPassword!"
                )

                verificar_cancelamento()
                aguardar(pagina)

                fila.put((
                    "log",
                    "Realizando login..."
                ))

                pagina.get_by_role(
                    "button",
                    name="Login"
                ).click()

                verificar_cancelamento()
                aguardar(pagina)

                fila.put((
                    "log",
                    "Validando resultado..."
                ))

                mensagem = pagina.locator("#flash")

                mensagem.wait_for(
                    state="visible"
                )

                verificar_cancelamento()

                texto = mensagem.inner_text()

                if "You logged into a secure area!" in texto:

                    sucesso = True

                    fila.put((
                        "log",
                        "LOGIN REALIZADO COM SUCESSO!"
                    ))

                    fila.put((
                        "status",
                        "Automacao concluida!",
                        VERDE
                    ))

                else:

                    raise Exception(
                        "Login nao confirmado."
                    )

            finally:

                # Fechar navegador antes de encerrar Playwright
                if navegador:

                    try:

                        navegador.close()

                        fila.put((
                            "log",
                            "Navegador encerrado."
                        ))

                    except Exception as erro:

                        fila.put((
                            "log",
                            f"Erro ao fechar navegador: {erro}"
                        ))

    except InterruptedError:

        cancelado = True

        fila.put((
            "log",
            "Automacao cancelada pelo usuario."
        ))

        fila.put((
            "status",
            "Automacao cancelada",
            VERMELHO
        ))

    except Exception as erro:

        fila.put((
            "log",
            f"ERRO: {str(erro)}"
        ))

        fila.put((
            "status",
            "Falha na automacao",
            VERMELHO
        ))

    finally:

        fila.put((
            "finished",
            sucesso,
            cancelado
        ))


# ==========================================
# INICIAR AUTOMACAO
# ==========================================

def iniciar_automacao():

    global executando

    if executando:
        return

    executando = True

    cancelar_evento.clear()

    botao_iniciar.config(
        state="disabled",
        text="EXECUTANDO..."
    )

    botao_cancelar.config(
        state="normal",
        text="CANCELAR AUTOMACAO"
    )

    atualizar_status(
        "Automacao em andamento...",
        AZUL
    )

    registrar_log(
        "Solicitacao de automacao recebida."
    )

    Thread(
        target=executar_robo,
        daemon=True
    ).start()


# ==========================================
# CANCELAR AUTOMACAO
# ==========================================

def cancelar_automacao():

    if not executando:
        return

    cancelar_evento.set()

    botao_cancelar.config(
        state="disabled",
        text="CANCELANDO..."
    )

    atualizar_status(
        "Solicitando cancelamento...",
        VERMELHO
    )

    registrar_log(
        "Solicitacao de cancelamento recebida."
    )


# ==========================================
# PROCESSAR MENSAGENS DO ROBO
# ==========================================

def processar_fila():

    global executando, total_execucoes

    try:

        while True:

            mensagem = fila.get_nowait()

            tipo = mensagem[0]

            if tipo == "log":

                registrar_log(mensagem[1])

            elif tipo == "status":

                atualizar_status(
                    mensagem[1],
                    mensagem[2]
                )

            elif tipo == "finished":

                executando = False

                botao_iniciar.config(
                    state="normal",
                    text="INICIAR AUTOMACAO"
                )

                botao_cancelar.config(
                    state="disabled",
                    text="CANCELAR AUTOMACAO"
                )

                total_execucoes += 1

                valor_execucoes.config(
                    text=f"{total_execucoes:02d}"
                )

                sucesso = mensagem[1]
                cancelado = mensagem[2]

                if cancelado:

                    atualizar_status(
                        "Execucao cancelada",
                        VERMELHO
                    )

                elif sucesso:

                    atualizar_status(
                        "Execucao finalizada com sucesso",
                        VERDE
                    )

                else:

                    atualizar_status(
                        "Execucao finalizada com erro",
                        VERMELHO
                    )

    except Empty:
        pass

    janela.after(
        100,
        processar_fila
    )


# ==========================================
# CABECALHO
# ==========================================

cabecalho = tk.Frame(
    janela,
    bg=FUNDO,
    pady=20
)

cabecalho.pack(
    fill="x",
    padx=30
)

tk.Label(
    cabecalho,
    text="WEBFLOW AUTOMATION",
    font=("Arial", 22, "bold"),
    fg=BRANCO,
    bg=FUNDO
).pack(anchor="w")

tk.Label(
    cabecalho,
    text="Painel de controle de automacoes RPA",
    font=("Arial", 11),
    fg=CINZA,
    bg=FUNDO
).pack(
    anchor="w",
    pady=5
)


# ==========================================
# CARDS DE INDICADORES
# ==========================================

indicadores = tk.Frame(
    janela,
    bg=FUNDO
)

indicadores.pack(
    fill="x",
    padx=30,
    pady=15
)


def criar_card(parent, titulo, valor):

    card = tk.Frame(
        parent,
        bg=PAINEL,
        padx=25,
        pady=20
    )

    card.pack(
        side="left",
        expand=True,
        fill="both",
        padx=8
    )

    tk.Label(
        card,
        text=titulo,
        fg=CINZA,
        bg=PAINEL,
        font=("Arial", 11)
    ).pack(anchor="w")

    numero = tk.Label(
        card,
        text=valor,
        fg=BRANCO,
        bg=PAINEL,
        font=("Arial", 25, "bold")
    )

    numero.pack(
        anchor="w",
        pady=10
    )

    return numero


valor_automacoes = criar_card(
    indicadores,
    "AUTOMACOES",
    "01"
)

valor_execucoes = criar_card(
    indicadores,
    "EXECUCOES",
    "00"
)

criar_card(
    indicadores,
    "TECNOLOGIA",
    "RPA"
)


# ==========================================
# AREA CENTRAL
# ==========================================

area = tk.Frame(
    janela,
    bg=PAINEL,
    padx=25,
    pady=20
)

area.pack(
    fill="both",
    expand=True,
    padx=38,
    pady=15
)

tk.Label(
    area,
    text="Central de execucao",
    font=("Arial", 16, "bold"),
    fg=BRANCO,
    bg=PAINEL
).pack(anchor="w")


status = tk.Label(
    area,
    text="● Sistema pronto para executar",
    fg=VERDE,
    bg=PAINEL,
    font=("Arial", 11)
)

status.pack(
    anchor="w",
    pady=15
)


# ==========================================
# BOTOES
# ==========================================

botao_iniciar = tk.Button(
    area,
    text="INICIAR AUTOMACAO",
    command=iniciar_automacao,
    bg=AZUL,
    fg=BRANCO,
    font=("Arial", 11, "bold"),
    padx=20,
    pady=12,
    relief="flat",
    cursor="hand2"
)

botao_iniciar.pack(
    anchor="w",
    pady=10
)


botao_cancelar = tk.Button(
    area,
    text="CANCELAR AUTOMACAO",
    command=cancelar_automacao,
    bg=VERMELHO,
    fg=BRANCO,
    font=("Arial", 10, "bold"),
    padx=20,
    pady=12,
    relief="flat",
    cursor="hand2",
    state="disabled"
)

botao_cancelar.pack(
    anchor="w",
    pady=10
)


# ==========================================
# AREA DE LOGS
# ==========================================

tk.Label(
    area,
    text="Historico de atividades",
    font=("Arial", 13, "bold"),
    fg=BRANCO,
    bg=PAINEL
).pack(
    anchor="w",
    pady=(25, 10)
)


logs = tk.Text(
    area,
    height=10,
    bg="#0B1220",
    fg="#4ADE80",
    font=("Consolas", 10),
    relief="flat",
    padx=10,
    pady=10
)

logs.pack(
    fill="both",
    expand=True
)


# ==========================================
# INICIALIZACAO
# ==========================================

registrar_log(
    "WebFlow Automation inicializado."
)

registrar_log(
    "Aguardando comando do usuario."
)

processar_fila()

janela.mainloop()
