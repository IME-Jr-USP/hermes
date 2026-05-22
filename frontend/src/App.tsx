import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import type { FormEvent, KeyboardEvent } from 'react'
import logo from './assets/logo.png'
import './App.css'

type ChatMessage = {
  id: number
  role: 'assistant' | 'user'
  content: string
  isStreaming?: boolean
}

const THINKING_LABELS = [
  'Pensando...',
  'Acessando o JupiterWeb...',
  'Consultando disciplinas...',
  'Olhando para todas as disciplinas...',
  'Pesquisando por Jupiter e caindo em imagens de planetas...',
  'Lendo todas bibliografias...',
  'Relembrando o que é uma disciplina optativa...',
  'Tentando descobrir a diferença de AAC e AEX...'
]

const MOCK_ASSISTANT_ANSWER =
  'Posso te ajudar a escolher com mais clareza. Para comparar disciplinas, eu olharia primeiro para quatro pontos: carga horária, pré-requisitos, avaliação e conexão com o seu objetivo no semestre. Se você me disser seu curso, período ideal e o tipo de matéria que procura, eu monto uma lista mais direcionada.'

const THINKING_LABEL_INTERVAL_MS = 1500
const THINKING_DURATION_MS = 5600
const STREAMING_INTERVAL_MS = 24
const INTRO_EXIT_DURATION_MS = 620
const INTRO_COMPOSER_DURATION_MS = 680
const MOTION_EASING = 'cubic-bezier(0.22, 1, 0.36, 1)'

function getRandomThinkingLabelIndex(currentIndex: number) {
  if (THINKING_LABELS.length <= 1) {
    return 0
  }

  let nextIndex = currentIndex

  while (nextIndex === currentIndex) {
    nextIndex = Math.floor(Math.random() * THINKING_LABELS.length)
  }

  return nextIndex
}

function App() {
  const [message, setMessage] = useState('')
  const [statusMessage, setStatusMessage] = useState('')
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [thinkingLabelIndex, setThinkingLabelIndex] = useState(0)
  const [isAssistantThinking, setIsAssistantThinking] = useState(false)
  const [isAssistantStreaming, setIsAssistantStreaming] = useState(false)
  const [isWelcomeExiting, setIsWelcomeExiting] = useState(false)
  const formRef = useRef<HTMLFormElement>(null)
  const messageInputRef = useRef<HTMLTextAreaElement>(null)
  const transcriptRef = useRef<HTMLDivElement>(null)
  const nextMessageIdRef = useRef(1)
  const pendingComposerRectRef = useRef<DOMRect | null>(null)
  const welcomeExitTimeoutRef = useRef<number | null>(null)
  const thinkingTimeoutRef = useRef<number | null>(null)
  const streamingIntervalRef = useRef<number | null>(null)

  const hasMessage = message.trim().length > 0
  const isAssistantBusy = isAssistantThinking || isAssistantStreaming
  const hasConversation = messages.length > 0 || isAssistantThinking
  const shouldShowWelcome = !hasConversation || isWelcomeExiting

  useLayoutEffect(() => {
    const messageInput = messageInputRef.current

    if (!messageInput) {
      return
    }

    if (!message) {
      messageInput.style.height = ''
      return
    }

    messageInput.style.height = 'auto'
    messageInput.style.height = `${messageInput.scrollHeight}px`
  }, [message])

  useLayoutEffect(() => {
    const previousRect = pendingComposerRectRef.current
    const composer = formRef.current

    if (!previousRect || !composer || !hasConversation) {
      return
    }

    pendingComposerRectRef.current = null

    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      return
    }

    const nextRect = composer.getBoundingClientRect()
    const translateX = previousRect.left - nextRect.left
    const translateY = previousRect.top - nextRect.top

    if (Math.abs(translateX) < 1 && Math.abs(translateY) < 1) {
      return
    }

    composer.animate(
      [
        { transform: `translate3d(${translateX}px, ${translateY}px, 0)` },
        { transform: 'translate3d(0, 0, 0)' },
      ],
      {
        duration: INTRO_COMPOSER_DURATION_MS,
        easing: MOTION_EASING,
      },
    )
  }, [hasConversation])

  useEffect(() => {
    if (!isAssistantThinking) {
      return
    }

    const labelInterval = window.setInterval(() => {
      setThinkingLabelIndex((currentIndex) => getRandomThinkingLabelIndex(currentIndex))
    }, THINKING_LABEL_INTERVAL_MS)

    return () => window.clearInterval(labelInterval)
  }, [isAssistantThinking])

  useEffect(() => {
    transcriptRef.current?.scrollTo({
      top: transcriptRef.current.scrollHeight,
      behavior: 'smooth',
    })
  }, [messages, isAssistantThinking])

  useEffect(() => {
    return () => {
      if (welcomeExitTimeoutRef.current !== null) {
        window.clearTimeout(welcomeExitTimeoutRef.current)
      }

      if (thinkingTimeoutRef.current !== null) {
        window.clearTimeout(thinkingTimeoutRef.current)
      }

      if (streamingIntervalRef.current !== null) {
        window.clearInterval(streamingIntervalRef.current)
      }
    }
  }, [])

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    const trimmedMessage = message.trim()

    if (!trimmedMessage || isAssistantBusy) {
      return
    }

    const isFirstMessage = !hasConversation

    if (isFirstMessage) {
      pendingComposerRectRef.current = formRef.current?.getBoundingClientRect() ?? null
      setIsWelcomeExiting(true)

      if (welcomeExitTimeoutRef.current !== null) {
        window.clearTimeout(welcomeExitTimeoutRef.current)
      }

      welcomeExitTimeoutRef.current = window.setTimeout(() => {
        setIsWelcomeExiting(false)
        welcomeExitTimeoutRef.current = null
      }, INTRO_EXIT_DURATION_MS)
    }

    const userMessage: ChatMessage = {
      id: nextMessageIdRef.current,
      role: 'user',
      content: trimmedMessage,
    }

    nextMessageIdRef.current += 1
    setMessages((currentMessages) => [...currentMessages, userMessage])
    setStatusMessage('Mensagem enviada. Hermes está pensando.')
    setMessage('')
    setThinkingLabelIndex(() => getRandomThinkingLabelIndex(-1))
    setIsAssistantThinking(true)
    messageInputRef.current?.focus()

    thinkingTimeoutRef.current = window.setTimeout(() => {
      const assistantMessageId = nextMessageIdRef.current

      nextMessageIdRef.current += 1

      setIsAssistantThinking(false)
      setIsAssistantStreaming(true)
      setStatusMessage('Hermes está respondendo.')
      setMessages((currentMessages) => [
        ...currentMessages,
        {
          id: assistantMessageId,
          role: 'assistant',
          content: '',
          isStreaming: true,
        },
      ])

      let characterIndex = 0

      streamingIntervalRef.current = window.setInterval(() => {
        characterIndex += 1

        setMessages((currentMessages) =>
          currentMessages.map((currentMessage) => {
            if (currentMessage.id !== assistantMessageId) {
              return currentMessage
            }

            return {
              ...currentMessage,
              content: MOCK_ASSISTANT_ANSWER.slice(0, characterIndex),
              isStreaming: characterIndex < MOCK_ASSISTANT_ANSWER.length,
            }
          }),
        )

        if (characterIndex >= MOCK_ASSISTANT_ANSWER.length) {
          if (streamingIntervalRef.current !== null) {
            window.clearInterval(streamingIntervalRef.current)
            streamingIntervalRef.current = null
          }

          setIsAssistantStreaming(false)
          setStatusMessage('Resposta concluída.')
        }
      }, STREAMING_INTERVAL_MS)

      thinkingTimeoutRef.current = null
    }, THINKING_DURATION_MS)
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key !== 'Enter' || event.shiftKey) {
      return
    }

    event.preventDefault()

    if (hasMessage && !isAssistantBusy) {
      formRef.current?.requestSubmit()
    }
  }

  return (
    <>
      <header className="app-header" aria-label="Cabeçalho do Hermes">
        <a className="app-brand" href="/" aria-label="Hermes">
          <img className="app-brand-mark" src={logo} width="48" height="48" alt="" />
          <span className="app-title">Hermes</span>
        </a>
      </header>

      <main className={hasConversation ? 'page-shell page-shell-chat' : 'page-shell'} aria-labelledby="page-title">
        <section
          className={hasConversation ? 'chat-surface is-active' : 'chat-surface'}
          aria-describedby={hasConversation ? undefined : 'welcome-message'}
        >
          {shouldShowWelcome && (
            <div className={isWelcomeExiting ? 'welcome is-exiting' : 'welcome'}>
              <div className="brand-lockup">
                <img className="brand-mark" src={logo} width="160" height="160" alt="" />
                <h1 id={hasConversation ? undefined : 'page-title'} className="brand-title">
                  Hermes
                </h1>
              </div>

              <div className="welcome-copy">
                <p id={hasConversation ? undefined : 'welcome-message'}>Qual matéria da USP vamos descobrir hoje?</p>
              </div>
            </div>
          )}

          {hasConversation && (
            <div className="transcript" ref={transcriptRef} aria-label="Conversa com Hermes">
              <h1 id="page-title" className="sr-only">
                Conversa com Hermes
              </h1>
              <div className="message-list">
                {messages.map((chatMessage) => (
                  <article
                    className={`message-row message-row-${chatMessage.role}`}
                    key={chatMessage.id}
                    aria-label={chatMessage.role === 'user' ? 'Sua mensagem' : 'Resposta do Hermes'}
                  >
                    {chatMessage.role === 'assistant' && (
                      <img className="message-logo" src={logo} width="36" height="36" alt="" />
                    )}
                    <div className="message-box">
                      <p>{chatMessage.content}</p>
                      {chatMessage.isStreaming && <span className="stream-caret" aria-hidden="true" />}
                    </div>
                  </article>
                ))}

                {isAssistantThinking && (
                  <article className="message-row message-row-assistant" aria-label="Hermes está pensando">
                    <div className="thinking-box" aria-live="polite">
                      <img className="thinking-logo" src={logo} width="56" height="56" alt="" />
                      <span className="thinking-label" key={thinkingLabelIndex}>
                        {THINKING_LABELS[thinkingLabelIndex]}
                      </span>
                    </div>
                  </article>
                )}
              </div>
            </div>
          )}

          <form
            ref={formRef}
            className="composer"
            aria-label="Enviar mensagem ao Hermes"
            onSubmit={handleSubmit}
          >
            <label className="sr-only" htmlFor="message-input">
              Mensagem
            </label>
            <textarea
              ref={messageInputRef}
              id="message-input"
              name="message"
              rows={1}
              autoComplete="off"
              placeholder="O que você deseja estudar no próximo semestre?"
              required
              disabled={isAssistantBusy}
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              onKeyDown={handleKeyDown}
            />
            <button type="submit" disabled={!hasMessage || isAssistantBusy}>
              {isAssistantBusy ? 'Aguarde' : 'Enviar'}
            </button>
            <p className="sr-only" id="composer-status" aria-live="polite">
              {statusMessage}
            </p>
          </form>
        </section>
      </main>
    </>
  )
}

export default App
