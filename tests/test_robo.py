import socket
from dataclasses import replace
from pathlib import Path
from threading import Event

import pytest

from config import Configuracao
from robo import RoboLogin, Situacao

URL_DEMO = "https://the-internet.herokuapp.com/login"
CFG_DEMO = Configuracao(
    url=URL_DEMO, usuario="tomsmith", senha="SuperSecretPassword!",  # credenciais públicas do site de teste
    headless=True, delay_ms=0, timeout_ms=15000,
)


def _site_acessivel():
    try:
        socket.create_connection(("the-internet.herokuapp.com", 443), timeout=5).close()
        return True
    except OSError:
        return False


precisa_internet = pytest.mark.skipif(not _site_acessivel(), reason="site de demonstração inacessível")


def test_cancelado_antes_de_comecar():
    cancelar = Event()
    cancelar.set()
    resultado = RoboLogin(CFG_DEMO, cancelar=cancelar).executar()
    assert resultado.situacao == Situacao.CANCELADO
    assert resultado.etapas_concluidas == []


def test_mensagem_amigavel_para_timeout():
    from playwright.sync_api import TimeoutError as PlaywrightTimeout
    assert "Tempo esgotado" in RoboLogin._mensagem_amigavel(PlaywrightTimeout("x"))


@pytest.mark.integracao
@precisa_internet
def test_login_com_sucesso():
    etapas = []
    resultado = RoboLogin(CFG_DEMO, ao_avancar=lambda i, t, e: etapas.append(e)).executar()
    assert resultado.situacao == Situacao.SUCESSO, resultado.mensagem
    assert etapas == RoboLogin.ETAPAS
    assert resultado.evidencia is None


@pytest.mark.integracao
@precisa_internet
def test_senha_errada_gera_falha_com_evidencia():
    resultado = RoboLogin(replace(CFG_DEMO, senha="senha-errada")).executar()
    assert resultado.situacao == Situacao.FALHA
    assert "Login não confirmado" in resultado.mensagem
    assert resultado.evidencia and Path(resultado.evidencia).exists()
    Path(resultado.evidencia).unlink()


@pytest.mark.integracao
@precisa_internet
def test_cancelamento_durante_execucao():
    cancelar = Event()

    def ao_avancar(indice, total, etapa):
        if indice == 2:
            cancelar.set()

    resultado = RoboLogin(replace(CFG_DEMO, delay_ms=200), ao_avancar=ao_avancar, cancelar=cancelar).executar()
    assert resultado.situacao == Situacao.CANCELADO
