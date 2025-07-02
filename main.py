import os
import io
import logging
import json
import docx
import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from sentence_transformers import SentenceTransformer, util
import torch

# Configuração Inicial
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Carregando Chaves e Modelos de IA
SEARCH_API_KEY = os.getenv('GOOGLE_API_KEY')
SEARCH_ENGINE_ID = os.getenv('SEARCH_ENGINE_ID')
DRIVE_CREDENTIALS_JSON = os.getenv('GOOGLE_CREDENTIALS_JSON')

print("Carregando modelo de IA para busca semântica...")
semantic_model = SentenceTransformer('google/mobilebert-uncased')
print("Modelo de IA carregado.")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Funções Auxiliares
def ler_texto_docx(file_stream):
    document = docx.Document(file_stream)
    return "\n".join([para.text for para in document.paragraphs if para.text.strip() != ""])

def fatiar_texto(texto, tamanho_fatia=500, sobreposicao=50):
    return [texto[i:i+tamanho_fatia] for i in range(0, len(texto), tamanho_fatia - sobreposicao)]

# ENDPOINTS DA API
@app.get("/")
def root():
    return {"status": "Agente Jurídico Híbrido Online"}

@app.get("/buscar_jurisprudencia")
def buscar_jurisprudencia_externa(q: str):
    # ... (código da busca externa)
    # (O código completo está omitido aqui para brevidade, mas use a versão da nossa última conversa)

@app.get("/buscar_no_meu_acervo")
def buscar_no_acervo_pessoal(q: str):
    logger.info(f"Recebido pedido para busca interna: '{q}'")
    if not DRIVE_CREDENTIALS_JSON:
        raise HTTPException(status_code=500, detail="Credenciais do Google Drive não configuradas no servidor.")

    try:
        creds_info = json.loads(DRIVE_CREDENTIALS_JSON)
        SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
        creds = service_account.Credentials.from_service_account_info(creds_info, scopes=SCOPES)
        service = build('drive', 'v3', credentials=creds)

        folder_name = 'Acervo_IA'
        query_folder = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results_folder = service.files().list(q=query_folder, pageSize=1, fields="files(id)").execute()
        items_folder = results_folder.get('files', [])

        if not items_folder: return {"mensagem": f"A pasta de acervo '{folder_name}' não foi encontrada.", "resultados": []}

        folder_id = items_folder[0]['id']
        query_files = f"'{folder_id}' in parents and trashed=false"
        results_files = service.files().list(q=query_files, fields="files(id, name, mimeType)").execute()
        items_files = results_files.get('files', [])

        if not items_files: return {"mensagem": "Nenhum arquivo encontrado no acervo.", "resultados": []}

        todas_as_fatias = []
        fontes_das_fatias = []
        for item in items_files:
            if 'vnd.openxmlformats-officedocument.wordprocessingml.document' in item['mimeType']:
                request = service.files().get_media(fileId=item['id'])
                file_stream = io.BytesIO()
                downloader = MediaIoBaseDownload(file_stream, request)
                done = False
                while not done: status, done = downloader.next_chunk()
                file_stream.seek(0)
                texto_documento = ler_texto_docx(file_stream)
                fatias_do_arquivo = fatiar_texto(texto_documento)
                todas_as_fatias.extend(fatias_do_arquivo)
                fontes_das_fatias.extend([item['name']] * len(fatias_do_arquivo))

        if not todas_as_fatias: return {"mensagem": "Nenhum arquivo .docx encontrado no acervo.", "resultados": []}

        vetores = semantic_model.encode(todas_as_fatias, convert_to_tensor=True)
        vetor_pergunta = semantic_model.encode(q, convert_to_tensor=True)
        similaridades = util.cos_sim(vetor_pergunta, vetores)[0]
        top_resultados = torch.topk(similaridades, k=3)

        resultados_finais = [{"trecho_relevante": todas_as_fatias[idx], "similaridade": score.item(), "documento_fonte": fontes_das_fatias[idx]} for score, idx in zip(top_resultados[0], top_resultados[1])]

        return {"mensagem": "Busca no acervo concluída.", "resultados": resultados_finais}
    except Exception as e:
        logger.error(f"Erro na busca interna: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro ao realizar a busca no acervo pessoal.")