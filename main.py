from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import os, json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

PROMPT = """
Você é um especialista em micologia. Analise a imagem enviada e responda APENAS em JSON válido, sem texto fora do JSON, no seguinte formato:

{
  "nome_provavel": "nome científico e popular do fungo",
  "confianca": "alta | média | baixa",
  "alternativas": ["outro fungo possível 1", "outro fungo possível 2"],
  "aviso": "mensagem se a imagem for inconclusiva, ou null se for clara",
  "descricao_curta": "1 frase descrevendo o fungo identificado"
}

Se a imagem não mostrar um fungo ou for muito ruim, retorne confianca "baixa" e explique no aviso.
"""

@app.post("/identificar")
async def identificar_fungo(imagem: UploadFile = File(...)):
    conteudo = await imagem.read()

    import PIL.Image
    import io
    img = PIL.Image.open(io.BytesIO(conteudo))

    resposta = model.generate_content([PROMPT, img])
    texto = resposta.text.strip()

    if texto.startswith("```"):
        texto = texto.split("```")[1]
        if texto.startswith("json"):
            texto = texto[4:]

    resultado = json.loads(texto)
    return resultado

@app.get("/")
def raiz():
    return {"status": "API de fungos funcionando"}
