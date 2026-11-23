import pytest

from config import ConfiguracaoInvalida, carregar_configuracao

VARIAVEIS = ["WEBFLOW_URL", "WEBFLOW_USUARIO", "WEBFLOW_SENHA", "WEBFLOW_HEADLESS",
             "WEBFLOW_DELAY_MS", "WEBFLOW_TIMEOUT_MS"]


@pytest.fixture
def ambiente_limpo(monkeypatch, tmp_path):
    for nome in VARIAVEIS:
        monkeypatch.delenv(nome, raising=False)
    return tmp_path / "inexistente.env"


def _definir(monkeypatch, **valores):
    padrao = {"WEBFLOW_URL": "https://exemplo.test/login", "WEBFLOW_USUARIO": "usuario", "WEBFLOW_SENHA": "segredo"}
    for nome, valor in {**padrao, **valores}.items():
        monkeypatch.setenv(nome, valor)


def test_falta_variavel_obrigatoria(ambiente_limpo, monkeypatch):
    monkeypatch.setenv("WEBFLOW_URL", "https://exemplo.test/login")
    with pytest.raises(ConfiguracaoInvalida, match="WEBFLOW_USUARIO, WEBFLOW_SENHA"):
        carregar_configuracao(ambiente_limpo)


def test_valores_padrao(ambiente_limpo, monkeypatch):
    _definir(monkeypatch)
    cfg = carregar_configuracao(ambiente_limpo)
    assert cfg.headless is False
    assert cfg.delay_ms == 800
    assert cfg.timeout_ms == 10000


@pytest.mark.parametrize("valor, esperado", [("true", True), ("SIM", True), ("1", True), ("false", False), ("", False)])
def test_headless(ambiente_limpo, monkeypatch, valor, esperado):
    _definir(monkeypatch, WEBFLOW_HEADLESS=valor)
    assert carregar_configuracao(ambiente_limpo).headless is esperado


def test_inteiro_invalido(ambiente_limpo, monkeypatch):
    _definir(monkeypatch, WEBFLOW_DELAY_MS="rápido")
    with pytest.raises(ConfiguracaoInvalida, match="WEBFLOW_DELAY_MS"):
        carregar_configuracao(ambiente_limpo)


def test_senha_nao_aparece_na_representacao(ambiente_limpo, monkeypatch):
    _definir(monkeypatch)
    cfg = carregar_configuracao(ambiente_limpo)
    assert "segredo" not in repr(cfg)
    assert "***" in repr(cfg)
