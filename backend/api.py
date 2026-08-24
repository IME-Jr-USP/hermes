import time

from agent import obter_agent, obter_resposta
from db import obter_banco_disciplinas
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from utils import get_logger

obter_banco_disciplinas()
logger = get_logger(__name__)

app = FastAPI()
agent = obter_agent()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # TODO
    allow_methods=["*"],
    allow_headers=["*"],
)


class MensagemRequest(BaseModel):
    mensagem: str
    conversa_id: str


@app.post("/api/chat")
async def chat(body: MensagemRequest, request: Request) -> dict:
    """Faz requisição para enviar mensagem para o agente, e retorna dicionário com a
    resposta obtida."""

    inicio = time.time()
    logger.info(
        "Requisição para chat (conversa_id='%s'): ip '%s'",
        body.conversa_id,
        request.client.host if request.client else None,
    )

    try:
        resposta = obter_resposta(agent, body.mensagem, body.conversa_id)
        duracao = time.time() - inicio
        logger.info("Resposta gerada (conversa_id='%s'): em %.2fs", body.conversa_id, duracao)
        return {"resposta": resposta}
    except Exception as e:
        duracao = time.time() - inicio
        logger.error("Erro ao gerar resposta (conversa_id='%s'): '%s' (em %.2fs)", body.conversa_id, e, duracao)

        raise
