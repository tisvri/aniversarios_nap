#TODO: Bibliotecas
import os
from dotenv import load_dotenv
import requests
from urllib.parse import urljoin
import pandas as pd
from datetime import datetime

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

#TODO: Variaveis e env

load_dotenv()

api_url = os.getenv("API_URL")
api_username = os.getenv('API_USERNAME')
api_password = os.getenv('API_PASSWORD')

username_email = os.getenv('EMAIL_USERNAME')
password_email = os.getenv('EMAIL_PASSWORD')
server_email = os.getenv('EMAIL_SERVER')
port_email = int(os.getenv('EMAIL_PORT'))
receptor = os.getenv('EMAIL_RECEPTOR')

proximo_mes = datetime.now().month + 1
if proximo_mes > 12:
    proximo_mes = 1


#TODO: Conectar com a Polo -> Feito

body = {
    "nome": api_username,
    "password":api_password
}

# Obtençao do token de acesso à polotrial
auth_url = urljoin(api_url, "/sessions")

response = requests.post(auth_url, json = body)

# Extraindo o token
token = response.json()["token"]

# Incorporando a string Bearer para inserir
if token:
    auth_token = "Bearer " + token
    # print(f"Auth Token: {auth_token}")
else:
    print("Falha ao obter o token.")
    
    
url_request = "https://api.polotrial.com"

headers = {"Authorization": auth_token}


#TODO: Rotas e dfs

rota_protocolo = url_request+"/protocolo?nested=true"
df_protocolo = requests.get(rota_protocolo, headers = headers).json()
df_protocolo = pd.DataFrame(df_protocolo)
df_protocolo_limpo = df_protocolo[['id', 'apelido_protocolo', 'status']]
df_protocolo_limpo.rename(columns={'id': 'co_protocolo'}, inplace=True)


rota_voluntarios = url_request+"/voluntarios?nested=true"
df_voluntarios = requests.get(rota_voluntarios, headers = headers).json()
df_voluntarios = pd.DataFrame(df_voluntarios)
df_voluntarios_limpo = df_voluntarios[['id', 'nome', 'contatos', 'data_nascimento', 'dados_centro']]
df_voluntarios_limpo.rename(columns={'id': 'co_voluntario'}, inplace=True)


rota_participantes = url_request+"/participantes?nested=true"
df_participantes = requests.get(rota_participantes, headers = headers).json()
df_participantes = pd.DataFrame(df_participantes)
df_participantes_limpo = df_participantes[['id', 'co_voluntario', 'co_protocolo', 'dados_status', 'numero_de_screening']]
df_participantes_limpo.rename(columns={'id': 'id_participantes'}, inplace=True)


df_1 = df_participantes_limpo[['co_voluntario']] 
df_1 = pd.merge(df_participantes_limpo, df_voluntarios_limpo, how = 'inner', on = 'co_voluntario')

df_geral = pd.merge(df_1, df_protocolo_limpo, how = 'inner', on = 'co_protocolo')
df_geral = df_geral.drop(columns=['co_protocolo'])


#TODO: Extrair ultimas infos

def extrair_ultima_informacao(x):
    if x is None:
        return None
    else:
        values_list = list(x.values())
        if len(values_list) == 0:
            return None
        else:
            return values_list[-1]
        
extrair_ultima_info = [
    'dados_centro',
    'status',
    'dados_status'
    
]

for coluna in extrair_ultima_info:
    if coluna in df_geral.columns:
        df_geral.loc[:, coluna] = df_geral[coluna].apply(extrair_ultima_informacao)
    else:
        print(f"A coluna '{coluna}' não existe no DataFrame.")


#TODO: DF de aniversarios do mes que vem.

df_geral['data_nascimento'] = pd.to_datetime(df_geral['data_nascimento'], errors='coerce')

df_aniver = df_geral[df_geral['data_nascimento'].dt.month == proximo_mes]
df_aniver = df_aniver[df_aniver['status'].isin(['Recrutamento aberto', 'Em Andamento'])]
df_aniver = df_aniver[df_aniver['dados_status'].isin(['Ativo'])]
protocolos = df_aniver['apelido_protocolo'].unique()
centro = df_aniver['dados_centro'].unique()
print(centro)


#TODO: Mandando email

try:
    msg = MIMEMultipart("alternative")
    msg['From'] = username_email
    msg['Bcc'] = receptor
    msg['Subject'] = 'Notificações de Aniversários'

    css_table = """
    <style>
        body {
            font-family: Arial, sans-serif;
        }
        h2, h3, h4 {
            color: #333;
            margin-bottom: 5px;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            font-size: 14px;
            margin-bottom: 20px;
        }
        th, td {
            border: 1px solid #dddddd;
            text-align: left;
            padding: 8px;
        }
        th {
            background-color: #86CBEE;
            text-align: center;
        }
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        tr:hover {
            background-color: #EC0E73;
        }
    </style>
    """

    corpo_html = f"<html><head>{css_table}</head><body>"
    corpo_html += "<h2>Aniversariantes do mês</h2>"

    for protocolo in df_aniver['apelido_protocolo'].unique():
        corpo_html += f"<hr /> <h3>Protocolo: {protocolo}</h3>"
        df_proto = df_aniver[df_aniver['apelido_protocolo'] == protocolo]

        for centro in df_proto['dados_centro'].unique():
            corpo_html += f"<h4>Centro: {centro}</h4>"
            df_centro = df_proto[df_proto['dados_centro'] == centro]
            df_centro = df_centro.drop(columns=['dados_centro', 'apelido_protocolo', 'dados_status', 'id_participantes'])
            df_centro.rename(columns={'status': 'status do protocolo'}, inplace=True)
            df_centro.rename(columns={'co_voluntario': 'Id do voluntario'}, inplace=True)
            df_centro.rename(columns={'numero_de_screening': 'Numero de screening'}, inplace=True)
            df_centro.rename(columns={'nome': 'Nome'}, inplace=True)
            df_centro.rename(columns={'contatos': 'Contatos'}, inplace=True)
            df_centro.rename(columns={'status do protocolo': 'Status do protocolo'}, inplace=True)
            df_centro.rename(columns={'data_nascimento': 'Data de nascimento'}, inplace=True)

            df_centro['Data de nascimento'] = df_centro['Data de nascimento'].dt.strftime('%d/%m/%Y')
            df_centro = df_centro.sort_values(by='Data de nascimento', ascending=True)


            if not df_centro.empty:
                corpo_html += df_centro.to_html(index=False, border=0, justify='left', classes='table', escape=False)

    corpo_html += "</body></html>"

    msg.attach(MIMEText(corpo_html, 'html'))

    with smtplib.SMTP(server_email, port_email) as server:
        server.starttls()
        server.login(username_email, password_email)
        server.send_message(msg)

    print("E-mail enviado com sucesso!")

except Exception as e:
    print(f"Erro ao enviar o e-mail: {e}")



