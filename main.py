from fastapi import FastAPI, UploadFile, File

from fastapi.middleware.cors import CORSMiddleware

from PIL import Image

import google.generativeai as genai

import io

import json

import os



# Configuração da IA

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

model = genai.GenerativeModel("gemini-1.5-flash")



PROMPT = """

Você é um especialista em micologia. 

Analise a imagem e responda APENAS em JSON válido:

{

  "nome_provavel": "nome científico e popular",
  
  "confianca": "alta | média | baixa",
  
  "alternativas": ["alternativa 1", "alternativa 2"],
  
  "aviso": "aviso ou null",
  
  "descricao_curta": "1 frase"
  
}

"""



app = FastAPI()



# Configuração CORS - Aberta para garantir o funcionamento entre domínios

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
        


        # Chamada ao Gemini

        resposta = model.generate_content([PROMPT, img])
        
        texto = resposta.text.strip()
        


        # Limpeza de possíveis marcações de Markdown na resposta da IA

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
            
            "aviso": f"Erro técnico: {str(e)}",
            
            "descricao_curta": "Não foi possível processar a imagem."
            
        }
        



































