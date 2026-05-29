# Notificações de Aniversários — NAP

Automação que envia um e-mail mensal com a lista de voluntários aniversariantes do mês seguinte, agrupados por protocolo e centro, para estudos clínicos ativos cadastrados na plataforma [Polo Trial](https://www.polotrial.com).

## Como funciona

1. No último dia útil de cada mês, o workflow do GitHub Actions é disparado automaticamente.
2. O script autentica na API do Polo Trial e coleta os dados de voluntários, protocolos e participantes.
3. Filtra os voluntários com aniversário no mês seguinte que estejam com status **Ativo** em protocolos **Em Andamento** ou com **Recrutamento aberto**.
4. Gera um e-mail HTML com as tabelas organizadas por protocolo e centro e o envia via SMTP.

## Fluxo do GitHub Actions

```
Cron diário (12:30 UTC)
        │
        ▼
Verifica se hoje é o último dia útil do mês
        │
   Sim  │  Não → encerra sem ação
        ▼
  Executa main.py
        │
        ▼
  Envia e-mail
```

## Pré-requisitos

- Python >= 3.12
- [UV](https://docs.astral.sh/uv/) para gerenciamento de dependências

## Instalação local

```bash
# Clone o repositório
git clone <url-do-repositório>
cd aniversarios_nap

# Crie e ative o ambiente virtual com UV
uv sync

# Crie o arquivo .env com as variáveis necessárias
cp .env.example .env
```

## Variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto (nunca o commite):

```env
API_URL=https://api.polotrial.com
API_USERNAME=seu_usuario
API_PASSWORD=sua_senha

EMAIL_USERNAME=seu@email.com
EMAIL_PASSWORD=sua_senha_email
EMAIL_SERVER=smtp.seuservidor.com
EMAIL_PORT=587
EMAIL_RECEPTOR=destinatario@email.com
```

Para execução via GitHub Actions, cadastre essas mesmas variáveis como **Secrets** no repositório:
`Settings → Secrets and variables → Actions → New repository secret`

| Secret | Descrição |
|---|---|
| `API_URL` | URL base da API Polo Trial |
| `API_USERNAME` | Usuário de autenticação da API |
| `API_PASSWORD` | Senha de autenticação da API |
| `EMAIL_USERNAME` | Endereço de e-mail remetente |
| `EMAIL_PASSWORD` | Senha do e-mail remetente |
| `EMAIL_SERVER` | Servidor SMTP |
| `EMAIL_PORT` | Porta SMTP (geralmente `587`) |
| `EMAIL_RECEPTOR` | Endereço de destino do e-mail |

## Execução local

```bash
uv run main.py
```

## Dependências

| Pacote | Uso |
|---|---|
| `pandas` | Manipulação dos DataFrames de voluntários e protocolos |
| `requests` | Chamadas à API Polo Trial |
| `python-dotenv` | Leitura das variáveis de ambiente |
| `python-dateutil` | Cálculo do último dia útil do mês |

## Estrutura do projeto

```
.
├── .github/
│   └── workflows/
│       └── main.yml       # Pipeline de automação
├── main.py                # Script principal
├── pyproject.toml         # Dependências e metadados do projeto
├── uv.lock                # Lock file do UV
├── .gitignore
└── README.md
```
