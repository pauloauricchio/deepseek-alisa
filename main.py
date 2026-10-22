
import os
import logging
import requests
from fastapi import FastAPI, Request

app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"


@app.post("/")
async def main(request: Request):
    body = await request.json()
    version = body.get("version", "1.0")
    session = body.get("session", {})
    request_data = body.get("request", {})
user_text = (
    request_data.get("original_utterance")
    or request_data.get("command")
    or ""
)

    if not user_text:
        answer = "Desculpe, não entendi a pergunta."
    elif not os.getenv("DEEPSEEK_API_KEY"):
        logger.error("A variável DEEPSEEK_API_KEY não está configurada.")
        answer = "O serviço de inteligência artificial está mal configurado."
    else:
        try:
            response = requests.post(
                DEEPSEEK_API_URL,
                headers={
                    "Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-flash",
                    "messages": [
    {
        "role": "system",
        "content": (
            "Você é Paulo IA, assistente de voz. "
            "Entenda português e russo. "
            "Responda sempre no mesmo idioma da pergunta. "
            "Use respostas naturais, claras e curtas, "
            "adequadas para serem faladas em voz alta. "
            "Não traduza, a menos que o usuário peça."
        )
    },
    {"role": "user", "content": user_text}
],
                    ],
                    "thinking": {"type": "disabled"},
                    "max_tokens": 300,
                    "stream": False
                },
                timeout=(3, 8)
            )

            if response.status_code != 200:
                logger.error(
                    "DeepSeek HTTP %s: %s",
                    response.status_code,
                    response.text[:500]
                )
                answer = "Desculpe, a inteligência artificial está temporariamente indisponível."
            else:
                data = response.json()
                choices = data.get("choices", [])
                answer = (
                    choices[0].get("message", {}).get("content", "")
                    if choices else ""
                )
                if not answer:
                    logger.error("Resposta sem conteúdo esperado: %s", str(data)[:500])
                    answer = "Desculpe, não recebi uma resposta válida."

        except requests.RequestException as exc:
            logger.error("Erro de conexão com o DeepSeek: %s", str(exc))
            answer = "Desculpe, não consegui conectar à inteligência artificial."
        except (ValueError, TypeError, IndexError, KeyError) as exc:
            logger.error("Erro ao interpretar resposta: %s", str(exc))
            answer = "Desculpe, ocorreu um erro ao processar a resposta."

    return {
        "version": version,
        "session": session,
        "response": {
            "end_session": False,
            "text": answer
        }
    }
