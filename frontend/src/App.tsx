import { useState } from "react";
import type { KeyboardEvent } from "react";

interface ChatResponse {
    resposta: string;
}

export default function ChatApp() {
    const [mensagem, setMensagem] = useState<string>("");
    const [resposta, setResposta] = useState<string>("");
    const [carregando, setCarregando] = useState<boolean>(false);
    const [erro, setErro] = useState<string>("");
    const [conversaId] = useState<string>(() => crypto.randomUUID());


    async function enviarMensagem(): Promise<void> {
        if (!mensagem.trim()) return;

        setCarregando(true);
        setErro("");
        setResposta("");

        try {
            const res = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    mensagem,
                    conversa_id: conversaId,
                }),
            });

            if (!res.ok) throw new Error("Erro na requisição");

            const data: ChatResponse = await res.json();
            setResposta(data.resposta);
        } catch (err) {
            setErro(err instanceof Error ? err.message : "Erro desconhecido");
        } finally {
            setCarregando(false);
        }
    }

    function handleKeyDown(e: KeyboardEvent<HTMLInputElement>): void {
        if (e.key === "Enter") enviarMensagem();
    }

    return (
        <div style={{ maxWidth: 500, margin: "60px auto", fontFamily: "sans-serif" }}>
            <h2>Chatbot</h2>

            <div style={{ display: "flex", gap: 8 }}>
                <input
                    type="text"
                    value={mensagem}
                    onChange={(e) => setMensagem(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Digite sua mensagem..."
                    style={{ flex: 1, padding: 8 }}
                />
                <button onClick={enviarMensagem} disabled={carregando}>
                    {carregando ? "Enviando..." : "Enviar"}
                </button>
            </div>

            {carregando && <p>Carregando resposta...</p>}
            {erro && <p style={{ color: "red" }}>Erro: {erro}</p>}
            {resposta && (
                <div style={{ marginTop: 20, padding: 12, background: "#f4f4f4", borderRadius: 6 }}>
                    {resposta}
                </div>
            )}
        </div>
    );
}
