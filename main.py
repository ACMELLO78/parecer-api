import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

# --- Configuração do Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:     %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)
# --- Fim da Configuração ---

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root(request: Request):
    client_host = request.client.host
    logger.info(f"Rota raiz '/' acessada por: {client_host}")
    return {"status": "API online"}

@app.get("/jurisprudencias")
def buscar_jurisprudencias(consulta: str, request: Request):
    client_host = request.client.host
    logger.info(f"ROTA /jurisprudencias ACESSADA por {client_host} com consulta='{consulta}'")

    try:
        if not consulta:
            logger.warning("Consulta recebida está vazia.")
            raise HTTPException(status_code=400, detail="Parâmetro 'consulta' não pode ser vazio.")

        response_data = {
            "status": "sucesso",
            "consulta_recebida": consulta,
            "dados_encontrados": [
                {"id": 1, "ementa": "Ementa de exemplo sobre licitação..."},
                {"id": 2, "ementa": "Outra ementa sobre o tema licitação..."},
            ]
        }
        logger.info(f"Retornando resposta de sucesso para a consulta: '{consulta}'")
        return response_data

    except Exception as e:
        logger.error(f"ERRO INESPERADO ao processar /jurisprudencias: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ocorreu um erro interno no servidor.")