"""Configuração lida do arquivo .env (nunca do código)."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
PASTA_LOGS = BASE_DIR / "logs"
PASTA_EVIDENCIAS = BASE_DIR / "evidencias"
ARQUIVO_LOG = PASTA_LOGS / "automacao.log"


class ConfiguracaoInvalida(Exception):
    """Variável obrigatória ausente ou com valor inválido no .env."""


def _booleano(valor, padrao=False):
    if valor is None or valor == "":
        return padrao
    return valor.strip().lower() in {"1", "true", "sim", "yes", "s"}


def _inteiro(nome, padrao):
    valor = os.getenv(nome, "").strip()
    if not valor:
        return padrao
    try:
        return int(valor)
    except ValueError:
        raise ConfiguracaoInvalida(f"{nome} deve ser um número inteiro (valor atual: {valor!r}).")


@dataclass(frozen=True)
class Configuracao:
    url: str
    usuario: str
    senha: str
    headless: bool = False
    delay_ms: int = 800
    timeout_ms: int = 10000

    def __repr__(self):
        # Evita que a senha apareça em logs ou mensagens de erro
        return (f"Configuracao(url={self.url!r}, usuario={self.usuario!r}, senha='***', "
                f"headless={self.headless}, delay_ms={self.delay_ms}, timeout_ms={self.timeout_ms})")


def carregar_configuracao(arquivo_env=BASE_DIR / ".env"):
    load_dotenv(arquivo_env, override=False)

    obrigatorias = ["WEBFLOW_URL", "WEBFLOW_USUARIO", "WEBFLOW_SENHA"]
    ausentes = [nome for nome in obrigatorias if not os.getenv(nome, "").strip()]
    if ausentes:
        raise ConfiguracaoInvalida(
            f"Variáveis ausentes: {', '.join(ausentes)}. "
            "Copie o arquivo .env.example para .env e preencha os valores."
        )

    return Configuracao(
        url=os.environ["WEBFLOW_URL"].strip(),
        usuario=os.environ["WEBFLOW_USUARIO"].strip(),
        senha=os.environ["WEBFLOW_SENHA"],
        headless=_booleano(os.getenv("WEBFLOW_HEADLESS")),
        delay_ms=_inteiro("WEBFLOW_DELAY_MS", 800),
        timeout_ms=_inteiro("WEBFLOW_TIMEOUT_MS", 10000),
    )
