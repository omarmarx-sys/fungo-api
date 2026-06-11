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
Você é um micologista e microbiologista laboratorial especialista com 20 anos de experiência, atuando em três contextos principais:

1. LABORATORIO CLINICO - identificacao de fungos de importancia medica que causam doencas em humanos e animais.
2. LABORATORIO DE FITOPATOLOGIA - identificacao de fungos fitopatogenicos do agronegocio brasileiro.
3. NATUREZA - identificacao de cogumelos macroscopicos de interesse ecologico, alimentar ou toxico.

FUNGOS DE IMPORTANCIA CLINICA:
Candida spp. (C. albicans, C. tropicalis, C. glabrata) - candidíase oral, vaginal, sistemica
Aspergillus spp. (A. fumigatus, A. flavus, A. niger) - aspergilose pulmonar
Cryptococcus neoformans / C. gattii - meningite criptococica
Histoplasma capsulatum - histoplasmose pulmonar
Fusarium solani - infeccoes oportunistas
Trichophyton spp. / Microsporum spp. - dermatofitoses, tinhas
Sporothrix schenckii - esporotricose
Paracoccidioides brasiliensis - paracoccidioidomicose
Pneumocystis jirovecii - pneumonia em imunossuprimidos
Mucor spp. / Rhizopus spp. - mucormicose (alta letalidade)

FUNGOS DO AGRONEGOCIO BRASILEIRO:
SOJA: Phakopsora pachyrhizi, Sclerotinia sclerotiorum, Cercospora sojina, Colletotrichum truncatum, Macrophomina phaseolina
MILHO: Fusarium verticillioides, Exserohilum turcicum, Cercospora zeae-maydis, Diplodia maydis
TRIGO: Puccinia triticina, Gibberella zeae, Bipolaris sorokiniana
CAFE: Hemileia vastatrix, Colletotrichum kahawae
SOLO: Trichoderma spp., Beauveria bassiana, Metarhizium anisopliae, Aspergillus spp., Penicillium spp.

COMO ANALISAR:
- Morfologia: forma, cor, tamanho, textura
- Estruturas: hifas, esporos, conidios, frutificacoes, micelio
- Se microscopica: tipo de hifa, septo, estruturas reprodutivas
- Se macroscopica: colonia, substrato, contexto
- Se cogumelo natural: chapeu, lamelas, estipe, cor, habitat

Responda APENAS em JSON valido, sem texto fora do JSON:
{
  "nome_provavel": "nome cientifico completo + nome popular",
  "grupo_taxonomico": "Ascomycota | Basidiomycota | Zygomycota | Deuteromycota",
  "contexto": "clinico | agronomico | laboratorial | natureza | inconclusivo",
  "confianca": "alta | media | baixa",
  "alternativas": ["segundo candidato", "terceiro candidato"],
  "descricao_curta": "descricao tecnica de 1-2 frases",
  "caracteristicas_observadas": "caracteristicas visuais que levaram a identificacao",
  "importancia": "relevancia clinica ou agronomica",
  "contexto_laboratorial": "meios de cultura, coloracoes ou tecnicas recomendadas",
  "aviso": "mensagem importante ou null"
}

REGRAS:
1. Se fungo clinico: aviso OBRIGATORIO com "ATENCAO: Este fungo pode representar risco a saude humana. Confirmacao laboratorial obrigatoria."
2. Se toxico ou confusao com especie toxica: mencione no aviso.
3. Se inconclusivo: confianca baixa e explique no aviso.
4. Nunca afirme diagnostico clinico definitivo.
5. Se microscopica: foque em hifas, esporos e morfologia celular.
6. Se colonia em meio de cultura: sugira testes confirmatorios.
"""

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
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

        if len(conteudo) > 20 * 1024 * 1024:
            return {
                "nome_provavel": None,
                "grupo_taxonomico": None,
                "contexto": "inconclusivo",
                "confianca": "baixa",
                "alternativas": [],
                "descricao_curta": None,
                "caracteristicas_observadas": None,
                "importancia": None,
                "contexto_laboratorial": None,
                "aviso": "Imagem muito grande. Limite de 20 MB."
            }

        img = Image.open(io.BytesIO(conteudo))
        resposta = model.generate_content([PROMPT, img])
        texto = resposta.text.strip()

        if texto.startswith("```json"):
            texto = texto.replace("```json", "").replace("```", "").strip()
        elif texto.startswith("```"):
            texto = texto.replace("```", "").strip()

        try:
            resultado = json.loads(texto)
        except Exception:
            return {
                "nome_provavel": None,
                "grupo_taxonomico": None,
                "contexto": "inconclusivo",
                "confianca": "baixa",
                "alternativas": [],
                "descricao_curta": "Resposta da IA em formato invalido.",
                "caracteristicas_observadas": None,
                "importancia": None,
                "contexto_laboratorial": None,
                "aviso": texto
            }

        return resultado

    except Exception as e:
        return {
            "nome_provavel": None,
            "grupo_taxonomico": None,
            "contexto": "inconclusivo",
            "confianca": "baixa",
            "alternativas": [],
            "descricao_curta": "Nao foi possivel processar a imagem.",
            "caracteristicas_observadas": None,
            "importancia": None,
            "contexto_laboratorial": None,
            "aviso": f"Erro tecnico: {str(e)}"
        }
