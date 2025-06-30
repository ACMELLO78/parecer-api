from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Consulta(BaseModel):
    consulta: str

@app.get("/")
def status():
    return {"status": "API online"}

@app.post("/buscar")
def buscar_jurisprudencias(consulta: Consulta):
    return {"consulta_recebida": consulta.consulta}
