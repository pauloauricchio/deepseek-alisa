
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
    user_text = body.get("request", {}).get("original_utterance", "")

    if not user_text:
        return {
            "version": version,
            "session": session,
            "response": {
                "end_session": False,
                "text": "Desculpe, não consegui entender a pergunta."
            }
        }

    api_key = os.getenv("DEEPSEEK_API_KEY")

    if not api_key:
        logger.error("DEEPSEEK_API_KEY não está configurada no Render.")
        answer = "O serviço de inteligência artificial está mal configurado."
    else:
        try:
            response = requests.post(
                DEEPSEEK_API_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-flash",
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "Responda em russo se o usuário falar russo; "
                                "caso contrário, responda no idioma usado "
                                "pelo usuário. Seja breve e claro, como um "
                                "assistente de voz."
                            )
                        },
                        {"role": "user", "content": user_text}
                    ],
                    "thinking": {"type": "disabled"},
                    "max_tokens": 200,
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
                answer = (
                    "Desculpe, o serviço de inteligência artificial "
                    "está temporariamente indisponível."
                )
            else:
                data = response.json()
                choices = data.get("choices", [])
                answer = (
                    choices[0].get("message", {}).get("content", "")
                    if choices else ""
                )

                if not answer:
                    logger.error(
                        "Resposta sem texto esperado: %s",
                        str(data)[:500]
                    )
                    answer = "Desculpe, não recebi uma resposta válida."

        except requests.RequestException as exc:
            logger.error("Erro de conexão com o DeepSeek: %s", str(exc))
            answer = (
                "Desculpe, não consegui conectar à inteligência "
                "artificial. Tente novamente."
            )
        except (ValueError, TypeError, IndexError, KeyError) as exc:
            logger.error("Erro ao interpretar a resposta: %s", str(exc))
            answer = "Desculpe, ocorreu um erro ao processar a resposta."

    return {
        "version": version,
        "session": session,
        "response": {
            "end_session": False,
            "text": answer
        }
    }
