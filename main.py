from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"status": "API online"}

@app.get("/jurisprudencias")
def buscar_jurisprudencias(consulta: str):
    return {"consulta_recebida": consulta}
