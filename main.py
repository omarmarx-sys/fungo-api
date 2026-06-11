from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import google.generativeai as genai
import io
import json
import os

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-2.0-flash")

PROMPT = """
Você é um micologista e microbiologista laboratorial especialista com 20 anos de experiência em identificação de fungos e microrganismos, com foco especial em fungos fitopatogênicos, fungos do solo agrícola, fungos de importância clínica e laboratorial, análise microscópica de estruturas fúngicas, cultivo em meios de cultura e laudos técnicos.

Ao analisar a imagem, observe atentamente:
- Morfologia: forma, cor, tamanho, textura da superfície
- Estruturas visíveis: hifas, esporos, conídios, frutificações, micélio
- Padrão de crescimento, coloração e pigmentação
- Se for imagem microscópica: tipo de hifa, septo, estruturas reprodutivas
- Se for imagem macroscópica: colônia, substrato, contexto ambiental
- Contexto laboratorial: meio de cultura, coloração utilizada, magnificação

Responda APENAS em JSON válido, sem texto fora do JSON:

{
  "nome_provavel": "nome científico completo + nome popular se houver",
  "confianca": "alta | média | baixa",
  "alternativas": ["segundo candidato mais provável", "terceiro candidato"],
  "descricao_curta": "descrição técnica de 1-2 frases sobre o fungo identificado",
  "caracteristicas_observadas": "quais características visuais e microscópicas levaram a essa identificação",
  "importancia_agronomica": "relevância para agricultura ou saúde, se aplicável",
  "contexto_laboratorial": "orientações sobre meios de cultura, colorações ou técnicas recomendadas para confirmação",
  "aviso": "mensagem se a imagem for inconclusiva, qualidade ruim ou não mostrar fungo — caso contrário null"
}

Se a imagem não mostrar um fungo claramente, retorne confianca "baixa" e explique no aviso.
Se a imagem for microscópica, foque em estruturas como hifas, esporos, conídios e morfologia celular.
Se a imagem for de colônia em meio de cultura, descreva a morfologia colonial e sugira testes confirmatórios.
Sempre que possível, indique o grupo taxonômico: Ascomycota, Basidiomycota, Zygomycota, etc.
"""

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def raiz():
    return {"status": "API de fungos funcionando"}

@app.post("/identificar")
async def identificar(imagem: UploadFile = File(...)):
    try:
        conteudo = await imagem.read()
        img = Image.open(io.BytesIO(conteudo))

        resposta = model.generate_content([PROMPT, img])
        texto = resposta.text.strip()

        if texto.startswith("```json"):
            texto = texto.replace("```json", "").replace("```", "").strip()
        elif texto.startswith("```"):
            texto = texto.replace("```", "").strip()

        resultado = json.loads(texto)
        return resultado

    except Exception as e:
        return {
            "nome_provavel": None,
            "confianca": "baixa",
            "alternativas": [],
            "descricao_curta": "Não foi possível processar a imagem.",
            "caracteristicas_observadas": None,
            "importancia_agronomica": None,
            "contexto_laboratorial": None,
            "aviso": f"Erro técnico: {str(e)}"
        }
