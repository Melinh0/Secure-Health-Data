from openai import OpenAI, OpenAIError

from .config import settings


class LLMError(Exception):
    pass


def chamar_llm(prompt: str, system_message: str | None = None, model: str | None = None) -> str:
    keys = settings.api_keys
    if not settings.llm_base_url:
        raise LLMError("LLM não configurado: preencha LLM_BASE_URL no arquivo .env")
    if not keys:
        raise LLMError("Nenhuma chave encontrada: preencha OLLAMA_API_KEY no arquivo .env")

    messages = []
    if system_message:
        messages.append({"role": "system", "content": system_message})
    messages.append({"role": "user", "content": prompt})

    ultimo_erro: Exception | None = None
    for chave in keys:
        try:
            client = OpenAI(api_key=chave, base_url=settings.llm_base_url, timeout=90, max_retries=0)
            resposta = client.chat.completions.create(
                model=model or settings.llm_model,
                messages=messages,
                temperature=0.3,
                max_tokens=2000,
            )
            conteudo = resposta.choices[0].message.content
            if conteudo and conteudo.strip():
                return conteudo
            ultimo_erro = LLMError("resposta vazia do modelo")
        except OpenAIError as erro:
            ultimo_erro = erro
            continue

    raise LLMError(f"Todas as chaves falharam. Último erro: {ultimo_erro}")
