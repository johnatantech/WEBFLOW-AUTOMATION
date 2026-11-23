"""Robô de login com Playwright, independente de interface.

A interface (Tkinter ou linha de comando) recebe o andamento por um callback
e pode pedir o cancelamento por um threading.Event.
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from logging.handlers import RotatingFileHandler
from threading import Event

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

import config

logger = logging.getLogger("webflow")

MENSAGEM_SUCESSO = "You logged into a secure area!"


class Situacao(str, Enum):
    SUCESSO = "sucesso"
    FALHA = "falha"
    CANCELADO = "cancelado"


class Cancelado(Exception):
    pass


@dataclass
class Resultado:
    situacao: Situacao
    mensagem: str
    duracao_s: float = 0.0
    evidencia: str | None = None
    etapas_concluidas: list[str] = field(default_factory=list)


def configurar_log():
    """Grava em logs/automacao.log (até 3 arquivos de 1 MB) e no terminal."""
    if logger.handlers:
        return
    config.PASTA_LOGS.mkdir(exist_ok=True)
    formato = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    arquivo = RotatingFileHandler(config.ARQUIVO_LOG, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    arquivo.setFormatter(formato)
    terminal = logging.StreamHandler()
    terminal.setFormatter(formato)

    logger.addHandler(arquivo)
    logger.addHandler(terminal)
    logger.setLevel(logging.INFO)


class RoboLogin:

    ETAPAS = [
        "Abrir navegador",
        "Acessar sistema",
        "Preencher usuário",
        "Preencher senha",
        "Entrar",
        "Validar acesso",
    ]

    def __init__(self, cfg, ao_avancar=None, cancelar=None):
        """
        cfg: Configuracao
        ao_avancar(indice, total, etapa): chamado ao iniciar cada etapa
        cancelar: threading.Event; quando acionado, o robô para na próxima checagem
        """
        self.cfg = cfg
        self.ao_avancar = ao_avancar or (lambda *_: None)
        self.cancelar = cancelar or Event()
        self._concluidas = []

    # ------------------------------------------------------------ fluxo

    def executar(self):
        inicio = time.perf_counter()
        logger.info("Execução iniciada em %s", self.cfg.url)

        try:
            with sync_playwright() as p:
                navegador = None
                pagina = None
                try:
                    self._etapa(0)
                    navegador = p.chromium.launch(headless=self.cfg.headless)
                    pagina = navegador.new_page()
                    pagina.set_default_timeout(self.cfg.timeout_ms)

                    self._etapa(1)
                    pagina.goto(self.cfg.url, wait_until="domcontentloaded", timeout=self.cfg.timeout_ms * 2)

                    self._etapa(2)
                    pagina.get_by_label("Username").fill(self.cfg.usuario)

                    self._etapa(3)
                    pagina.get_by_label("Password").fill(self.cfg.senha)

                    self._etapa(4)
                    pagina.get_by_role("button", name="Login").click()

                    self._etapa(5)
                    aviso = pagina.locator("#flash")
                    aviso.wait_for(state="visible")
                    texto = aviso.inner_text()
                    if MENSAGEM_SUCESSO not in texto:
                        mensagem_sistema = texto.replace("×", "").strip()
                        raise AssertionError(f"Login não confirmado. Mensagem do sistema: {mensagem_sistema}")

                    self._concluidas.append(self.ETAPAS[5])
                    return self._resultado(Situacao.SUCESSO, "Login realizado com sucesso.", inicio)

                except Cancelado:
                    return self._resultado(Situacao.CANCELADO, "Execução cancelada pelo usuário.", inicio)

                except (PlaywrightTimeout, PlaywrightError, AssertionError) as erro:
                    evidencia = self._capturar_evidencia(pagina)
                    mensagem = self._mensagem_amigavel(erro)
                    return self._resultado(Situacao.FALHA, mensagem, inicio, evidencia)

                finally:
                    if navegador is not None:
                        navegador.close()
                        logger.info("Navegador encerrado.")

        except PlaywrightError as erro:
            # Falha antes de abrir o navegador (ex.: Chromium não instalado)
            return self._resultado(Situacao.FALHA, self._mensagem_amigavel(erro), inicio)

    # ------------------------------------------------------------ auxiliares

    def _etapa(self, indice):
        if indice > 0:
            self._concluidas.append(self.ETAPAS[indice - 1])
            self._aguardar()
        self._verificar_cancelamento()
        etapa = self.ETAPAS[indice]
        logger.info("Etapa %d/%d: %s", indice + 1, len(self.ETAPAS), etapa)
        self.ao_avancar(indice, len(self.ETAPAS), etapa)

    def _aguardar(self):
        # Event.wait em vez de time.sleep: o cancelamento é atendido na hora
        if self.cancelar.wait(self.cfg.delay_ms / 1000):
            raise Cancelado

    def _verificar_cancelamento(self):
        if self.cancelar.is_set():
            raise Cancelado

    def _capturar_evidencia(self, pagina):
        if pagina is None:
            return None
        try:
            config.PASTA_EVIDENCIAS.mkdir(exist_ok=True)
            caminho = config.PASTA_EVIDENCIAS / f"falha_{datetime.now():%Y%m%d_%H%M%S}.png"
            pagina.screenshot(path=str(caminho), full_page=True)
            logger.info("Evidência salva em %s", caminho)
            return str(caminho)
        except PlaywrightError:
            logger.warning("Não foi possível capturar a evidência da falha.")
            return None

    @staticmethod
    def _mensagem_amigavel(erro):
        texto = str(erro)
        if "Executable doesn't exist" in texto:
            return "Navegador do Playwright não instalado. Rode: playwright install chromium"
        if isinstance(erro, PlaywrightTimeout):
            return "Tempo esgotado: o sistema não respondeu ou um elemento não foi encontrado."
        if "net::ERR" in texto:
            return "Não foi possível acessar o sistema. Verifique a URL e a conexão."
        if isinstance(erro, AssertionError):
            return texto
        return f"Erro na automação: {texto.splitlines()[0]}"

    def _resultado(self, situacao, mensagem, inicio, evidencia=None):
        duracao = time.perf_counter() - inicio
        nivel = logging.INFO if situacao == Situacao.SUCESSO else logging.WARNING
        logger.log(nivel, "Execução finalizada: %s (%.1f s). %s", situacao.value, duracao, mensagem)
        return Resultado(situacao, mensagem, duracao, evidencia, list(self._concluidas))
