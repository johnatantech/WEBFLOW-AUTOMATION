"""Painel de controle do robô em Tkinter."""

import os
import sys
import tkinter as tk
from datetime import datetime
from queue import Empty, Queue
from threading import Event, Thread
from tkinter import ttk

import config
from config import ConfiguracaoInvalida, carregar_configuracao
from robo import RoboLogin, Situacao, configurar_log

FUNDO = "#111827"
PAINEL = "#1F2937"
BORDA = "#374151"
AZUL = "#2563EB"
BRANCO = "#F9FAFB"
CINZA = "#9CA3AF"
VERDE = "#22C55E"
VERMELHO = "#EF4444"
AMARELO = "#F59E0B"
FONTE = "Segoe UI" if sys.platform.startswith("win") else "Helvetica"

CORES_SITUACAO = {Situacao.SUCESSO: VERDE, Situacao.FALHA: VERMELHO, Situacao.CANCELADO: AMARELO}


class Painel:

    def __init__(self, janela):
        self.janela = janela
        self.fila = Queue()
        self.cancelar = Event()
        self.executando = False
        self.contagem = {Situacao.SUCESSO: 0, Situacao.FALHA: 0, Situacao.CANCELADO: 0}
        self.ultima_evidencia = None

        janela.title("WebFlow Automation")
        janela.geometry("980x700")
        janela.minsize(860, 600)
        janela.configure(bg=FUNDO)

        self._montar_cabecalho()
        self._montar_indicadores()
        self._montar_central()
        self._carregar_configuracao()
        self._processar_fila()

    # ------------------------------------------------------------ layout

    def _montar_cabecalho(self):
        quadro = tk.Frame(self.janela, bg=FUNDO)
        quadro.pack(fill="x", padx=32, pady=(24, 8))
        tk.Label(quadro, text="WebFlow Automation", font=(FONTE, 20, "bold"), fg=BRANCO, bg=FUNDO).pack(anchor="w")
        self.label_alvo = tk.Label(quadro, text="", font=(FONTE, 10), fg=CINZA, bg=FUNDO)
        self.label_alvo.pack(anchor="w", pady=(2, 0))

    def _card(self, pai, titulo):
        card = tk.Frame(pai, bg=PAINEL, padx=20, pady=14, highlightbackground=BORDA, highlightthickness=1)
        card.pack(side="left", expand=True, fill="both", padx=6)
        tk.Label(card, text=titulo, fg=CINZA, bg=PAINEL, font=(FONTE, 10)).pack(anchor="w")
        valor = tk.Label(card, text="0", fg=BRANCO, bg=PAINEL, font=(FONTE, 22, "bold"))
        valor.pack(anchor="w", pady=(4, 0))
        return valor

    def _montar_indicadores(self):
        quadro = tk.Frame(self.janela, bg=FUNDO)
        quadro.pack(fill="x", padx=26, pady=8)
        self.valor_sucessos = self._card(quadro, "Sucessos")
        self.valor_falhas = self._card(quadro, "Falhas")
        self.valor_cancelados = self._card(quadro, "Cancelamentos")
        self.valor_duracao = self._card(quadro, "Última duração")
        self.valor_duracao.config(text="-")

    def _montar_central(self):
        area = tk.Frame(self.janela, bg=PAINEL, padx=24, pady=18, highlightbackground=BORDA, highlightthickness=1)
        area.pack(fill="both", expand=True, padx=32, pady=(8, 24))

        self.status = tk.Label(area, text="", font=(FONTE, 11, "bold"), bg=PAINEL)
        self.status.pack(anchor="w")

        estilo = ttk.Style()
        estilo.theme_use("clam")
        estilo.configure("Robo.Horizontal.TProgressbar", troughcolor=FUNDO, background=AZUL,
                         bordercolor=PAINEL, lightcolor=AZUL, darkcolor=AZUL)
        self.barra = ttk.Progressbar(area, style="Robo.Horizontal.TProgressbar", maximum=len(RoboLogin.ETAPAS))
        self.barra.pack(fill="x", pady=(10, 4))
        self.label_etapa = tk.Label(area, text="", font=(FONTE, 9), fg=CINZA, bg=PAINEL)
        self.label_etapa.pack(anchor="w")

        botoes = tk.Frame(area, bg=PAINEL)
        botoes.pack(anchor="w", pady=14)
        self.botao_iniciar = self._botao(botoes, "Iniciar automação", AZUL, self.iniciar)
        self.botao_cancelar = self._botao(botoes, "Cancelar", VERMELHO, self.cancelar_execucao, estado="disabled")
        self.botao_evidencia = self._botao(botoes, "Abrir evidência da falha", "#4B5563", self.abrir_evidencia, estado="disabled")

        tk.Label(area, text="Histórico", font=(FONTE, 11, "bold"), fg=BRANCO, bg=PAINEL).pack(anchor="w", pady=(6, 6))
        self.logs = tk.Text(area, height=10, bg=FUNDO, fg="#D1D5DB", font=("Consolas", 10), relief="flat",
                            padx=10, pady=10, state="disabled", insertbackground=BRANCO)
        self.logs.pack(fill="both", expand=True)
        for situacao, cor in CORES_SITUACAO.items():
            self.logs.tag_configure(situacao.value, foreground=cor)

    def _botao(self, pai, texto, cor, comando, estado="normal"):
        botao = tk.Button(pai, text=texto, command=comando, fg=BRANCO, activebackground=cor,
                          activeforeground=BRANCO, disabledforeground="#6B7280", font=(FONTE, 10, "bold"),
                          padx=18, pady=9, relief="flat", bd=0, highlightthickness=0)
        botao.cor = cor
        botao.pack(side="left", padx=(0, 10))
        self._habilitar(botao, estado == "normal")
        return botao

    @staticmethod
    def _habilitar(botao, ativo, texto=None):
        """Botão desabilitado fica cinza, para não parecer clicável."""
        botao.config(state="normal" if ativo else "disabled", bg=botao.cor if ativo else BORDA,
                     cursor="hand2" if ativo else "arrow")
        if texto:
            botao.config(text=texto)

    # ------------------------------------------------------------ ações

    def _carregar_configuracao(self):
        try:
            self.cfg = carregar_configuracao()
            modo = "navegador oculto" if self.cfg.headless else "navegador visível"
            self.label_alvo.config(text=f"Sistema: {self.cfg.url}  ({modo})")
            self._status("Pronto para executar", VERDE)
            self._log("Configuração carregada do .env.")
        except ConfiguracaoInvalida as erro:
            self.cfg = None
            self.label_alvo.config(text="Sem configuração")
            self._status("Configuração pendente", AMARELO)
            self._log(str(erro), Situacao.FALHA.value)
            self._habilitar(self.botao_iniciar, False)

    def iniciar(self):
        if self.executando or self.cfg is None:
            return
        self.executando = True
        self.cancelar.clear()
        self.barra["value"] = 0
        self._habilitar(self.botao_iniciar, False, "Executando...")
        self._habilitar(self.botao_cancelar, True, "Cancelar")
        self._habilitar(self.botao_evidencia, False)
        self._status("Automação em andamento", AZUL)
        self._log("Execução iniciada.")

        robo = RoboLogin(
            self.cfg,
            ao_avancar=lambda i, total, etapa: self.fila.put(("etapa", i, total, etapa)),
            cancelar=self.cancelar,
        )
        # O robô roda fora da thread da interface; a comunicação é só pela fila
        Thread(target=lambda: self.fila.put(("fim", robo.executar())), daemon=True).start()

    def cancelar_execucao(self):
        if self.executando:
            self.cancelar.set()
            self._habilitar(self.botao_cancelar, False, "Cancelando...")
            self._status("Cancelando...", AMARELO)

    def abrir_evidencia(self):
        if not self.ultima_evidencia or not os.path.exists(self.ultima_evidencia):
            return
        if sys.platform.startswith("win"):
            os.startfile(self.ultima_evidencia)
        elif sys.platform == "darwin":
            os.system(f'open "{self.ultima_evidencia}"')
        else:
            os.system(f'xdg-open "{self.ultima_evidencia}"')

    # ------------------------------------------------------------ fila (thread da interface)

    def _processar_fila(self):
        try:
            while True:
                mensagem = self.fila.get_nowait()
                if mensagem[0] == "etapa":
                    _, indice, total, etapa = mensagem
                    self.barra["value"] = indice
                    self.label_etapa.config(text=f"Etapa {indice + 1} de {total}: {etapa}")
                    self._log(etapa)
                elif mensagem[0] == "fim":
                    self._finalizar(mensagem[1])
        except Empty:
            pass
        self.janela.after(100, self._processar_fila)

    def _finalizar(self, resultado):
        self.executando = False
        self.contagem[resultado.situacao] += 1
        self.valor_sucessos.config(text=self.contagem[Situacao.SUCESSO])
        self.valor_falhas.config(text=self.contagem[Situacao.FALHA])
        self.valor_cancelados.config(text=self.contagem[Situacao.CANCELADO])
        self.valor_duracao.config(text=f"{resultado.duracao_s:.1f} s")

        if resultado.situacao == Situacao.SUCESSO:
            self.barra["value"] = len(RoboLogin.ETAPAS)

        cor = CORES_SITUACAO[resultado.situacao]
        self._status(resultado.mensagem, cor)
        self._log(resultado.mensagem, resultado.situacao.value)

        self.ultima_evidencia = resultado.evidencia
        if resultado.evidencia:
            self._log(f"Evidência: {resultado.evidencia}")
        self._habilitar(self.botao_evidencia, bool(resultado.evidencia))

        self._habilitar(self.botao_iniciar, True, "Iniciar automação")
        self._habilitar(self.botao_cancelar, False, "Cancelar")

    # ------------------------------------------------------------ utilitários

    def _status(self, texto, cor):
        self.status.config(text=f"● {texto}", fg=cor)

    def _log(self, texto, tag=None):
        self.logs.config(state="normal")
        self.logs.insert(tk.END, f"[{datetime.now():%H:%M:%S}] {texto}\n", tag)
        self.logs.see(tk.END)
        self.logs.config(state="disabled")


if __name__ == "__main__":
    configurar_log()
    raiz = tk.Tk()
    Painel(raiz)
    raiz.mainloop()
