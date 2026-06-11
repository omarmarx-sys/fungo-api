from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import io, json, os
import google.generativeai as genai

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

PROMPT = """Você é um especialista em micologia. Analise a imagem e responda APENAS em JSON válido:
{
  "nome_provavel": "nome científico e popular do fungo",
  "confianca": "alta | média | baixa",
  "alternativas": ["alternativa 1", "alternativa 2"],
  "aviso": null,
  "descricao_curta": "1 frase descrevendo o fungo"
}"""

@app.post("/identificar")
async def identificar(imagem: UploadFile = File(...)):
    conteudo = await imagem.read()
    img = Image.open(io.BytesIO(conteudo))
    resposta = model.generate_content([PROMPT, img])
    texto = resposta.text.strip().replace("```json", "").replace("```", "").strip()
    return json.loads(texto)

@app.get("/")
def raiz():
    return {"status": "API de fungos funcionando"}
