import os
import io
import logging
import json
import docx
import fitz # PyMuPDF
import faiss
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google.oauth2 import service_account
from googleapiclient.discovery import build
from sentence_transformers import SentenceTransformer, util
import torch
from google.cloud import storage

# --- Configuração Inicial ---
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# --- Carregando Chaves e Nomes ---
SEARCH_API_KEY = os.getenv('GOOGLE_API_KEY')
SEARCH_ENGINE_ID = os.getenv('SEARCH_ENGINE_ID')
BUCKET_NAME = 'memoria-agente-mello-12345' # O nome do seu bucket
INDEX_FILE_NAME = 'acervo_index.faiss'
DATA_FILE_NAME = 'fatias_e_fontes.json'

# --- Carregando Modelos e a Memória (Na Inicialização) ---
app = FastAPI()

# Variáveis globais para armazenar a memória carregada
index = None
todas_as_fatias = []
fontes_das_fatias = []
semantic_model = None

@app.on_event("startup")
def carregar_memoria_e_modelo():
    global index, todas_as_fatias, fontes_das_fatias, semantic_model
    
    try:
        logger.info("Iniciando carregamento do modelo de IA...")
        semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("Modelo de IA carregado com sucesso.")

        logger.info(f"Baixando arquivos de memória do bucket '{BUCKET_NAME}'...")
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)

        # Download do índice FAISS
        blob_index = bucket.blob(INDEX_FILE_NAME)
        blob_index.download_to_filename(INDEX_FILE_NAME)
        index = faiss.read_index(INDEX_FILE_NAME)
        logger.info(f"Índice FAISS ('{INDEX_FILE_NAME}') carregado com {index.ntotal} vetores.")

        # Download dos dados JSON
        blob_data = bucket.blob(DATA_FILE_NAME)
        json_data_string = blob_data.download_as_text()
        data = json.loads(json_data_string)
        todas_as_fatias = data['fatias']
        fontes_das_fatias = data['fontes']
        logger.info(f"Dados JSON ('{DATA_FILE_NAME}') carregados com {len(todas_as_fatias)} fatias.")

    except Exception as e:
        logger.error(f"ERRO CRÍTICO NA INICIALIZAÇÃO: Não foi possível carregar a memória. {e}", exc_info=True)
        # Em um app real, poderíamos ter um mecanismo de fallback.
        # Aqui, a busca no acervo simplesmente não funcionará.
        index = None 

# --- Endpoints da API ---
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def root():
    return {"status": "Agente Jurídico Híbrido Online e Pronto"}

@app.get("/buscar_jurisprudencia")
def buscar_jurisprudencia_externa(q: str):
    logger.info(f"Recebido pedido para busca externa: '{q}'")
    if not SEARCH_API_KEY or not SEARCH_ENGINE_ID:
        raise HTTPException(status_code=500, detail="Chaves da API de Busca não configuradas.")
    try:
        service = build("customsearch", "v1", developerKey=SEARCH_API_KEY)
        res = service.cse().list(q=q, cx=SEARCH_ENGINE_ID, num=5).execute()
        resultados = [{"titulo": item.get('title'), "link": item.get('link'), "resumo": item.get('snippet')} for item in res.get('items', [])]
        return {"resultados": resultados}
    except Exception as e:
        logger.error(f"Erro na busca externa: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro ao realizar a busca externa.")

@app.get("/buscar_no_meu_acervo")
def buscar_no_acervo_pessoal(q: str):
    logger.info(f"Recebido pedido para busca interna: '{q}'")
    if index is None or not todas_as_fatias:
        raise HTTPException(status_code=503, detail="A memória do acervo pessoal não está disponível ou falhou ao carregar.")
    
    try:
        vetor_pergunta = semantic_model.encode(q, convert_to_tensor=True)
        
        # A busca agora é local e super rápida!
        distancias, indices = index.search(np.array([vetor_pergunta.cpu()]), k=3)
        
        resultados_finais = []
        for i, idx in enumerate(indices[0]):
            if idx != -1: # FAISS retorna -1 se não encontrar vizinhos suficientes
                resultados_finais.append({
                    "trecho_relevante": todas_as_fatias[idx],
                    "similaridade": 1 - distancias[0][i], # Converte distância L2 para uma noção de similaridade
                    "documento_fonte": fontes_das_fatias[idx]
                })
        
        return {"resultados": resultados_finais}
    except Exception as e:
        logger.error(f"Erro na busca interna: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro ao realizar a busca no acervo pessoal.")
