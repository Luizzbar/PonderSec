from typing import Any, Dict, List
import sys
import os
from openCHA.llms import BaseLLM
from openCHA.utils import get_from_dict_or_env
from pydantic import model_validator

class OpenAILLM(BaseLLM):
    """
    OpenCHA Adapter for OpenAI-Compatible APIs (Groq, DeepSeek, etc).
    """

    # Adicionamos modelos da Groq aqui para passar na validação
    models: Dict = {
        "deepseek-chat": 32768,
        "llama3-70b-8192": 8192,   # Modelo da Groq
        "mixtral-8x7b-32768": 32768, # Modelo da Groq
        "gpt-4": 8192,
        "gpt-3.5-turbo": 4096,
    }
    api_key: str = ""
    llm_model: Any = None
    max_tokens: int = 150

    @model_validator(mode="before")
    def validate_environment(cls, values: Dict) -> Dict:
        if 'openai' in sys.modules:
            values["llm_model"] = sys.modules['openai']
        else:
            import importlib
            values["llm_model"] = importlib.import_module("openai")

        openai_api_key = get_from_dict_or_env(
            values, "openai_api_key", "OPENAI_API_KEY"
        )
        values["api_key"] = openai_api_key
        return values

    def get_model_names(self) -> List[str]:
        return self.models.keys()

    def is_max_token(self, model_name, query) -> bool:
        return False 

    def _parse_response(self, response) -> str:
        return response.choices[0].message['content']

    def _prepare_prompt(self, prompt) -> Any:
        return [{"role": "user", "content": prompt}]

    def generate(self, query: str, **kwargs: Any) -> str:
        # Pega o nome do modelo passado nos argumentos
        model_name = "gpt-3.5-turbo" # Fallback
        
        if "model_name" in kwargs:
            model_name = kwargs["model_name"]
            # Removemos a lógica de forçar deepseek aqui para permitir Groq

        # Se o framework tentar usar GPT, forçamos o Llama 3 (Groq)
        if "gpt" in model_name:
            model_name = "llama3-70b-8192"

        stop = kwargs.get("stop", None)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        
        openai_lib = self.llm_model
        
        # A URL Base será definida no services.py
        openai_lib.api_key = self.api_key
        
        print(f"\n--- [OpenCHA Adapter] Enviando request ---")
        print(f"URL Base: {openai_lib.api_base}")
        print(f"Modelo: {model_name}")
        print("-" * 30)

        query_msg = self._prepare_prompt(query)
        
        try:
            response = openai_lib.ChatCompletion.create(
                model=model_name,
                messages=query_msg,
                max_tokens=max_tokens,
                stop=stop
            )
            return self._parse_response(response)
        except Exception as e:
            print(f"ERRO LLM: {e}")
            raise e