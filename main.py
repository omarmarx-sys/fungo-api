````python
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import google.generativeai as genai
import io
import json
import os

# =========================
# CONFIGURAÇÃO GEMINI
# =========================

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

model = genai.GenerativeModel("gemini-1.5-flash")

PROMPT = """
Você é um especialista em micologia.

Analise a imagem e responda APENAS JSON válido:

{
  "nome_provavel": "nome científico e popular",
  "confianca": "alta",
  "alternativas": ["opção 1", "opção 2"],
  "aviso": "texto ou null",
  "descricao_curta": "descrição curta"
}
"""

# =========================
# FASTAPI
# =========================

app = FastAPI()

# =========================
# CORS
# =========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://fungo-site.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# ROTA RAIZ
# =========================

@app.get("/")
def raiz():
    return {"status": "API de fungos funcionando"}

# =========================
# IDENTIFICAÇÃO
# =========================

@app.post("/identificar")
async def identificar(imagem: UploadFile = File(...)):

    try:

        conteudo = await imagem.read()

        img = Image.open(io.BytesIO(conteudo))

        resposta = model.generate_content(
            [PROMPT, img]
        )

        texto = resposta.text.strip()

        if texto.startswith("```json"):
            texto = texto.replace("```json", "").replace("```", "").strip()

        resultado = json.loads(texto)

        return resultado

    except Exception as e:

        return {
            "nome_provavel": None,
            "confianca": "baixa",
            "alternativas": [],
            "aviso": str(e),
            "descricao_curta": "Erro ao processar imagem"
        }
````
