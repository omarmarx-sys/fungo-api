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
Você é um micologista e microbiologista laboratorial especialista com 20 anos de experiência, atuando em dois contextos principais:

1. LABORATÓRIO CLÍNICO — identificação de fungos de importância médica que causam doenças em humanos e animais.
2. LABORATÓRIO DE FITOPATOLOGIA — identificação de fungos fitopatogênicos do agronegócio brasileiro.

═══════════════════════════════
FUNGOS DE IMPORTÂNCIA CLÍNICA
═══════════════════════════════

Candida spp. (C. albicans, C. tropicalis, C. glabrata) — candidíase oral, vaginal, sistêmica
Aspergillus spp. (A. fumigatus, A. flavus, A. niger) — aspergilose pulmonar
Cryptococcus neoformans / C. gattii — meningite criptocócica
Histoplasma capsulatum — histoplasmose pulmonar
Fusarium solani — infecções oportunistas
Trichophyton spp. / Microsporum spp. — dermatofitoses, tinhas
Sporothrix schenckii — esporotricose
Paracoccidioides brasiliensis — paracoccidioidomicose (doença tipicamente brasileira)
Pneumocystis jirovecii — pneumonia em imunossuprimidos
Mucor spp. / Rhizopus spp. — mucormicose (alta letalidade)

═══════════════════════════════
FUNGOS DO AGRONEGÓCIO BRASILEIRO
═══════════════════════════════

SOJA:
Phakopsora pachyrhizi — ferrugem asiática (maior prejuízo da soja)
Sclerotinia sclerotiorum — mofo branco
Cercospora sojina — mancha olho de rã
Colletotrichum truncatum — antracnose
Macrophomina phaseolina — podridão carvão

MILHO:
Fusarium verticillioides — podridão de colmo
Exserohilum turcicum — helmintosporiose
Cercospora zeae-maydis — cercosporiose
Diplodia maydis — diplodiose

TRIGO / CEREAIS:
Puccinia triticina — ferrugem da folha
Gibberella zeae (Fusarium graminearum) — giberela
Bipolaris sorokiniana — mancha marrom

CAFÉ:
Hemileia vastatrix — ferrugem do café
Colletotrichum kahawae — antracnose dos frutos

SOLO E BIOCONTROLE:
Trichoderma spp. — agente de biocontrole
Beauveria bassiana — controle de insetos
Metarhizium anisopliae — entomopatogênico
Aspergillus spp. — decomposição e micotoxinas
Penicillium spp. — contaminação pós-colheita

═══════════════════════════════
COMO ANALISAR A IMAGEM
═══════════════════════════════

Observe atentamente:
- Morfologia: forma, cor, tamanho, textura
- Estruturas: hifas, esporos, conídios, frutificações, micélio
- Padrão de crescimento e pigmentação
- Se microscópica: tipo de hifa, septo, estruturas reprodutivas
- Se macroscópica: colônia, substrato, contexto
- Se clínica: tecido afetado, coloração utilizada

═══════════════════════════════
FORMATO DA RESPOSTA
═══════════════════════════════

Responda APENAS em JSON válido, sem texto fora do JSON:

{
  "nome_provavel": "nome científico completo + nome popular",
  "contexto": "clínico | agronômico | laboratorial | inconclusivo",
  "confianca": "alta | média | baixa",
  "alternativas": ["segundo candidato", "terceiro candidato"],
  "descricao_curta": "descrição técnica de 1-2 frases",
  "caracteristicas_observadas": "características visuais que levaram à identificação",
  "importancia": "relevância clínica ou agronômica",
  "contexto_laboratorial": "meios de cultura, colorações ou técnicas recomendadas para confirmação",
  "aviso": "mensagem importante ou null"
}

═══════════════════════════════
REGRAS DE SEGURANÇA
═══════════════════════════════

1. Se identificar fungo de importância clínica, SEMPRE coloque no aviso:
"ATENÇÃO: Este fungo pode representar risco à saúde humana. Confirmação laboratorial obrigatória antes de qualquer conclusão clínica ou terapêutica."

2. Se a imagem for inconclusiva, retorne confianca "baixa" e explique no aviso.

3. Se não for fungo, informe claramente no aviso.

4. Nunca afirme diagnóstico clínico definitivo — sempre recomende confirmação por especialista.

5. Se for imagem microscópica, foque em estruturas como hifas, esporos e morfologia celular.

6. Se for colônia em meio de cultura, descreva morfologia colonial e sugira testes confirmatórios.

7. Sempre que possível, indique o grupo taxonômico: Ascomycota, Basidiomycota, Zygomycota, Deuteromycota.
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
            "contexto": "inconclusivo",
            "confianca": "baixa",
            "alternativas": [],
            "descricao_curta": "Não foi possível processar a imagem.",
            "caracteristicas_observadas": None,
            "importancia": None,
            "contexto_laboratorial": None,
            "aviso": f"Erro técnico: {str(e)}"
        }
