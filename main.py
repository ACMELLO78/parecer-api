from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

app = FastAPI()

# (opcional) permitir requisições externas
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ou seu domínio específico
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔹 ROTA RAIZ - usada para teste de status
@app.get("/")
def root():
    return {"status": "API online"}

# 🔹 ENDPOINT FUNCIONAL
@app.get("/jurisprudencias")
def buscar_jurisprudencias(consulta: Optional[str] = None):
    return {"consulta_recebida": consulta}
