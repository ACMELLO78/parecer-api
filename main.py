from fastapi import FastAPI, Request

app = FastAPI()

@app.get("/")
def raiz():
    return {"mensagem": "API funcionando"}

@app.post("/buscar-jurisprudencia")
async def buscar_jurisprudencias(request: Request):
    dados = await request.json()
    consulta = dados.get("consulta", "não informado")
    return {"consulta_recebida": consulta}
