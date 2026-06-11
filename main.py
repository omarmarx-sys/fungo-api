from fastapi import FastAPI, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import google.generativeai as genai
import os, json
import PIL.Image
import io

app = FastAPI()

@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    if request.method == "OPTIONS":
        response = JSONResponse({})
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
        return response
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

PROMPT = """Você é um especialista em micologia. Analise a imagem e responda APENAS em JSON válido:
{
  "nome_provavel": "nome científico e popular",
  "confianca": "alta | média | baixa",
  "alternativas": ["alternativa 1", "alternativa 2"],
  "aviso": null,
  "descricao_curta": "1 frase"
}"""

@app.post("/identificar")
async def identificar_fungo(imagem: UploadFile = File(...)):
    conteudo = await imagem.read()
    img = PIL.Image.open(io.BytesIO(conteudo))
    resposta = model.generate_content([PROMPT, img])
    texto = resposta.text.strip()
    if texto.startswith("```"):
        texto = texto.split("```")[1]
        if texto.startswith("json"):
            texto = texto[4:]
    return json.loads(texto)

@app.get("/")
def raiz():
    return {"status": "API de fungos funcionando"}
