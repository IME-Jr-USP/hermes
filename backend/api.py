from agent import obter_agent, obter_resposta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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
async def chat(req: MensagemRequest):
    resposta = obter_resposta(agent, req.mensagem, req.conversa_id)
    return {"resposta": resposta[0]["text"]}
