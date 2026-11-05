import time
from contextlib import asynccontextmanager

from agent import obter_agent, obter_resposta
from config import settings
from constants import MAX_LENGTH_CONVERSA_ID, MAX_LENGTH_MENSAGEM
from db import obter_banco_disciplinas
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from utils import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Inicializando banco de disciplinas")
    collection = obter_banco_disciplinas()

    logger.info("Inicializando agente Hermes")
    app.state.agent = obter_agent()

    logger.info("Realizando consulta de aquecimento")
    if collection.count() > 0:
        collection.query(
            query_texts=["aquecimento"],
            n_results=1,
            include=["metadatas"],
        )

    logger.info("Inicialização concluída.")

    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MensagemRequest(BaseModel):
    mensagem: str = Field(min_length=1, max_length=MAX_LENGTH_MENSAGEM)
    conversa_id: str = Field(min_length=1, max_length=MAX_LENGTH_CONVERSA_ID)


@app.post("/api/chat")
def chat(body: MensagemRequest, request: Request) -> dict[str, str]:
    """Faz requisição para enviar mensagem para o agente, e retorna dicionário com a
    resposta obtida."""

    inicio = time.time()
    logger.info("Requisição para chat (conversa_id='%s'): ip '%s'", body.conversa_id, request.client.host if request.client else None)

    try:
        resposta = obter_resposta(body.mensagem, body.conversa_id)
        duracao = time.time() - inicio
        logger.info("Resposta gerada (conversa_id='%s'): em %.2fs", body.conversa_id, duracao)
        return {"resposta": resposta}
    except Exception:
        duracao = time.time() - inicio
        logger.exception("Erro ao gerar resposta (conversa_id='%s'): em %.2fs", body.conversa_id, duracao)

        raise HTTPException(
            status_code=500,
            detail="Não foi possível processar sua mensagem.",
        )
