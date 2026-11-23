"""Execução do robô pela linha de comando (útil para agendamento)."""

import argparse
import sys
from dataclasses import replace

from config import ConfiguracaoInvalida, carregar_configuracao
from robo import RoboLogin, Situacao, configurar_log


def main():
    parser = argparse.ArgumentParser(description="Robô de login web com Playwright.")
    parser.add_argument("--headless", action="store_true", help="executa sem abrir a janela do navegador")
    args = parser.parse_args()

    configurar_log()
    try:
        cfg = carregar_configuracao()
    except ConfiguracaoInvalida as erro:
        print(f"Configuração inválida: {erro}")
        return 2

    if args.headless:
        cfg = replace(cfg, headless=True)

    resultado = RoboLogin(cfg).executar()

    print(f"\nResultado: {resultado.situacao.value.upper()} em {resultado.duracao_s:.1f} s")
    print(resultado.mensagem)
    if resultado.evidencia:
        print(f"Evidência: {resultado.evidencia}")

    # Código de saída permite que agendadores identifiquem falhas
    return 0 if resultado.situacao == Situacao.SUCESSO else 1


if __name__ == "__main__":
    sys.exit(main())
