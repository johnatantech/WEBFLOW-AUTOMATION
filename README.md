# WebFlow Automation

Sistema de automação de processos WebFlow desenvolvido em Python, utilizando Playwright para automação do navegador e Tkinter para interface gráfica.

## Funcionalidades

- Dashboard com interface gráfica.
- Automação de login.
- Execução automatizada pelo navegador.
- Controle de execução.
- Cancelamento da automação.
- Atualização de status da execução.
- Encerramento automático do navegador.

## Tecnologias utilizadas

- Python
- Playwright
- Tkinter

## Instalação

Clone o repositório:

```bash
git clone https://github.com/johnatantech/WEBFLOW-AUTOMATION.git
```

Entre na pasta:

```bash
cd WEBFLOW-AUTOMATION
```

Crie um ambiente virtual:

```bash
python -m venv venv
```

Ative o ambiente virtual no Windows:

```powershell
.\venv\Scripts\Activate.ps1
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

Instale os navegadores do Playwright:

```bash
playwright install
```

## Como executar

Execute o dashboard:

```bash
python dashboard.py
```

## Estrutura do projeto

```text
WEBFLOW-AUTOMATION/
├── dashboard.py
├── login_automation.py
├── main.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Desenvolvedor

**Johnatan Flores**

GitHub: https://github.com/johnatantech
LinkedIn: https://www.linkedin.com/in/johnatan-flores-67595a221

## Versão

v1.0.0

---

Projeto desenvolvido para automatização de processos utilizando Python e Playwright.