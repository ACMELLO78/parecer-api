import os
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env para o ambiente
load_dotenv()

# --- Configuração do Logging ---
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# --- Carregando as Chaves Secretas do Ambiente ---
API_KEY = os.getenv('GOOGLE_API_KEY')
SEARCH_ENGINE_ID = os.getenv('SEARCH_ENGINE_ID')

# --- Verificação Inicial ---
if not API_KEY or not SEARCH_ENGINE_ID:
    logger.error("ERRO CRÍTICO: Variáveis de ambiente GOOGLE_API_KEY e/ou SEARCH_ENGINE_ID não encontradas.")
    # Em um cenário real, poderíamos impedir a aplicação de iniciar.

# --- Criação do Aplicativo FastAPI ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Função de Busca (A mesma que testamos no Colab) ---
def buscar_no_jusbrasil(termo_de_busca: str, num_resultados: int = 5):
    logger.info(f"Iniciando a busca por: '{termo_de_busca}'...")
    if not API_KEY or not SEARCH_ENGINE_ID:
        raise HTTPException(status_code=500, detail="Chaves da API não foram configuradas no servidor.")
    try:
        service = build("customsearch", "v1", developerKey=API_KEY)
        res = service.cse().list(
            q=termo_de_busca, cx=SEARCH_ENGINE_ID, num=num_resultados
        ).execute()

        resultados_formatados = [
            {"titulo": item.get('title'), "link": item.get('link'), "resumo": item.get('snippet')}
            for item in res.get('items', [])
        ]
        return resultados_formatados
    except Exception as e:
        logger.error(f"ERRO durante a busca na API do Google: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro ao realizar a busca externa.")

# --- Endpoints da API ---
@app.get("/")
def root():
    return {"status": "Serviço de Busca Jurídica Online"}

@app.get("/buscar_jurisprudencia")
def endpoint_de_busca(q: str):
    if not q:
        raise HTTPException(status_code=400, detail="O parâmetro de busca 'q' não pode ser vazio.")

    resultados = buscar_no_jusbrasil(termo_de_busca=q)

    if not resultados:
        return {"mensagem": "Nenhum resultado encontrado.", "resultados": []}

    return {"mensagem": f"{len(resultados)} resultados encontrados.", "resultados": resultados}