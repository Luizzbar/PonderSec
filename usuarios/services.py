import os
import sys
import openai 

# Imports do framework...
try:
    from openCHA import openCHA
except ImportError:
    try:
        from openCHA.openCHA import openCHA
    except ImportError:
        from open_cha_cybersec.src.openCHA.openCHA import openCHA

class DualEngine:
    def __init__(self, groq_key, gemini_key):
        # --- CONFIGURAÇÃO 1: GROQ (Via OpenAI Client) ---
        openai.api_key = groq_key
        # URL Oficial da Groq
        openai.api_base = "https://api.groq.com/openai/v1" 
        
        os.environ["OPENAI_API_KEY"] = groq_key
        os.environ["OPENAI_API_BASE"] = "https://api.groq.com/openai/v1"

        # Engine A (Groq fingindo ser OpenAI)
        self.engine_groq = openCHA(
            verbose=True,
            planner_llm="openai", 
            response_generator_llm="openai" 
        )

        # Engine B (Gemini)
        os.environ["GEMINI_API_KEY"] = gemini_key
        self.engine_gemini = openCHA(
            verbose=True,
            planner_llm="gemini",
            response_generator_llm="gemini"
        )

    def gerar_duelo(self, texto_usuario, historico=[]):
        print(f"--- [Arena] Iniciando duelo: Groq vs Gemini ---")
        
        try:
            # 1. Groq (Llama 3)
            # Passamos o nome do modelo Llama 3
            resp_groq = self.engine_groq.run(
                query=texto_usuario,
                chat_history=historico,
                available_tasks=[], 
                use_history=bool(historico),
                model_name="llama3-70b-8192"  # <--- Modelo da Groq
            )
            
            # 2. Gemini
            resp_gemini = self.engine_gemini.run(
                query=texto_usuario,
                chat_history=historico,
                available_tasks=[], 
                use_history=bool(historico)
            )
            
            return {
                "gpt": str(resp_groq),   # 'gpt' no banco agora guarda Groq
                "gemini": str(resp_gemini)
            }
            
        except Exception as e:
            print(f"ERRO ARENA: {e}")
            # Em vez de retornar erro para o usuário, retornamos um aviso amigável
            # caso seja erro de saldo ou cota.
            return {"erro": str(e)}