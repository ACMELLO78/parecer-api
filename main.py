from fastapi import FastAPI, HTTPException
import requests
from bs4 import BeautifulSoup

app = FastAPI()

@app.get("/jurisprudencias")
def buscar_jurisprudencias(consulta: str):
    consulta_url = consulta.replace(" ", "+")
    url = f"https://www.jusbrasil.com.br/jurisprudencia/busca?q={consulta_url}"

    headers = {'User-Agent': 'Mozilla/5.0'}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise HTTPException(status_code=500, detail=str(err))

    soup = BeautifulSoup(response.text, 'html.parser')
    cards = soup.find_all('div', {'class': 'BaseSnippetWrapper'})[:5]

    resultados = []
    for card in cards:
        titulo = card.find('h2', {'class': 'BaseSnippetWrapper-title'})
        ementa = card.find('p', {'class': 'BaseSnippetWrapper-excerpt'})
        link = card.find('a', href=True)
        if titulo and ementa and link:
            resultados.append({
                "titulo": titulo.get_text(strip=True),
                "ementa": ementa.get_text(strip=True),
                "link": "https://www.jusbrasil.com.br" + link['href']
            })
    return resultados
