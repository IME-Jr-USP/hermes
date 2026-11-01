import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { Navigate, useLocation } from 'react-router';

import { ArrowUp, Hourglass } from 'lucide-react';

import Skeleton, { SkeletonTheme } from 'react-loading-skeleton';
import 'react-loading-skeleton/dist/skeleton.css';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

import './ConversationPage.css';

/* ========================================
   DEMO
======================================== */

const DEMO_RESPONSE = `
Encontrei **3 disciplinas** que correspondem aos seus interesses em inteligência artificial e aprendizado de máquina. Todas possuem atividades no período da tarde e podem ser consideradas para sua grade.

## Disciplinas recomendadas

### 1. Introdução ao Aprendizado de Máquina

**IME — Instituto de Matemática e Estatística**

| Informação | Detalhes |
|---|---|
| Código | MAC0460 |
| Créditos | 4 créditos-aula |
| Horário | Segundas e quartas, 14h–15h40 |

Excelente opção para aprofundar seus conhecimentos em **modelos estatísticos, algoritmos de aprendizado e programação em Python**.

- **Área:** Inteligência Artificial
- **Nível:** Intermediário
- **Compatibilidade:** Alta

[Consultar disciplina no JúpiterWeb →](https://uspdigital.usp.br/jupiterweb/)

---

### 2. Ética e Inteligência Artificial

**FFLCH — Faculdade de Filosofia, Letras e Ciências Humanas**

| Informação | Detalhes |
|---|---|
| Código | FLF0389 |
| Créditos | 4 créditos-aula |
| Horário | Quintas-feiras, 14h–17h40 |

Aborda os impactos sociais de sistemas automatizados, incluindo **justiça algorítmica, vieses em modelos e regulação de inteligência artificial**.

É uma boa opção para complementar a formação técnica com uma perspectiva interdisciplinar.

[Consultar disciplina no JúpiterWeb →](https://uspdigital.usp.br/jupiterweb/)

---

### 3. Sistemas Inteligentes e Automação

**POLI — Escola Politécnica**

| Informação | Detalhes |
|---|---|
| Código | PCS3542 |
| Créditos | 4 créditos-aula |
| Horário | Sextas-feiras, 13h15–16h50 |

Apresenta aplicações de sistemas inteligentes em problemas de engenharia, com foco em **automação, visão computacional e agentes inteligentes**.

[Consultar disciplina no JúpiterWeb →](https://uspdigital.usp.br/jupiterweb/)

---

## Minha recomendação

Considerando seu interesse em algoritmos e fundamentos de inteligência artificial, eu priorizaria **Introdução ao Aprendizado de Máquina**. Ela parece oferecer a conexão mais direta entre seus conhecimentos atuais de computação e os tópicos que você pretende estudar.

A disciplina de Ética e Inteligência Artificial seria um bom complemento, especialmente para ampliar sua perspectiva sobre as aplicações e implicações dessas tecnologias.

> **Atenção:** horários, pré-requisitos e disponibilidade de vagas podem mudar. Confirme os oferecimentos no JúpiterWeb antes de realizar sua matrícula.
`;

async function getRecommendations(query) {
	if (!query.trim()) {
		throw new Error('Consulta vazia.');
	}

	await new Promise((resolve) => setTimeout(resolve, 2500));

	return DEMO_RESPONSE;
}

/* ========================================
   USER QUERY
======================================== */

function UserQuery({ query, elementRef }) {
	return (
		<section ref={elementRef} className="user-query">
			<div className="user-query-header">
				<span>Sua mensagem</span>
			</div>

			<p>{query}</p>
		</section>
	);
}

/* ========================================
   ASSISTANT
======================================== */

function AssistantHeading({ loading }) {
	return (
		<div className="assistant-heading">
			<span className={`assistant-indicator ${loading ? 'is-loading' : ''}`} />

			<span className="assistant-name">Hermes</span>

			<span className="assistant-status">
				{loading
					? 'Consultando catálogo do JúpiterWeb e sintetizando opções...'
					: 'Assistente de Disciplinas'}
			</span>
		</div>
	);
}

function LoadingSkeleton() {
	return (
		<SkeletonTheme baseColor="#efede9" highlightColor="#f7f5f1" duration={2.0}>
			<div className="loading-skeleton" aria-hidden="true">
				<Skeleton width="100%" />
				<Skeleton width="92%" />
				<Skeleton width="76%" />
				<Skeleton width="38%" />
				<Skeleton width="100%" />
				<Skeleton width="96%" />
				<Skeleton width="68%" />
				<Skeleton width="100%" />
				<Skeleton width="85%" />
				<Skeleton width="57%" />
			</div>
		</SkeletonTheme>
	);
}

function AssistantResponse({ response }) {
	return (
		<div className="assistant-response">
			<ReactMarkdown remarkPlugins={[remarkGfm]}>{response}</ReactMarkdown>
		</div>
	);
}

/* ========================================
   CONVERSATION INPUT
======================================== */

function ConversationInput({ loading, onSubmit }) {
	const [message, setMessage] = useState('');
	const textareaRef = useRef(null);

	function handleSubmit(event) {
		event.preventDefault();

		const text = message.trim();

		if (!text || loading) return;

		onSubmit(text);
		setMessage('');
	}

	useEffect(() => {
		if (!loading) {
			textareaRef.current?.focus();
		}
	}, [loading]);

	return (
		<div className="conversation-bottom">
			<form className="conversation-input" onSubmit={handleSubmit}>
				{loading && (
					<Hourglass
						size={14}
						strokeWidth={1.5}
						className="conversation-input-icon"
						aria-hidden="true"
					/>
				)}

				<textarea
					value={message}
					ref={textareaRef}
					onChange={(event) => setMessage(event.target.value)}
					placeholder={
						loading ? 'Aguarde a resposta para continuar...' : 'Continue conversando...'
					}
					aria-label="Enviar mensagem ao Hermes"
					rows={1}
					onKeyDown={(event) => {
						if (
							event.key === 'Enter' &&
							!event.shiftKey &&
							!event.nativeEvent.isComposing
						) {
							event.preventDefault();
							event.currentTarget.form?.requestSubmit();
						}
					}}
					disabled={loading}
				/>

				<button
					type="submit"
					aria-label="Enviar mensagem"
					disabled={!message.trim() || loading}
				>
					<ArrowUp size={20} strokeWidth={1.8} />
				</button>
			</form>

			<p className="conversation-disclaimer">
				Hermes pode cometer imprecisões. Verifique os códigos e turmas no JúpiterWeb antes
				da matrícula.
			</p>
		</div>
	);
}

/* ========================================
   CONVERSATION PAGE
======================================== */

function ConversationPage() {
	const location = useLocation();
	const initialQuery = location.state?.query?.trim() ?? '';

	/* Histórico da conversa */

	const [history, setHistory] = useState(() =>
		initialQuery ? [{ question: initialQuery, answer: null, error: null }] : [],
	);

	/* Requisição atualmente em execução */

	const [request, setRequest] = useState(() =>
		initialQuery ? { question: initialQuery, index: 0 } : null,
	);

	/* Scroll automático */

	const latestQueryRef = useRef(null);
	const [scrollTargetIndex, setScrollTargetIndex] = useState(null);

	/* ========================================
	   EXECUTAR REQUISIÇÃO
	======================================== */

	useEffect(() => {
		if (!request) return;

		let cancelled = false;

		async function loadRecommendations() {
			try {
				const result = await getRecommendations(request.question);

				if (cancelled) return;

				setHistory((current) =>
					current.map((item, index) =>
						index === request.index ? { ...item, answer: result, error: null } : item,
					),
				);
			} catch (err) {
				if (cancelled) return;

				setHistory((current) =>
					current.map((item, index) =>
						index === request.index ? { ...item, error: err.message } : item,
					),
				);
			} finally {
				if (!cancelled) {
					setRequest(null);
				}
			}
		}

		loadRecommendations();

		return () => {
			cancelled = true;
		};
	}, [request]);

	/* ========================================
	   SCROLL AUTOMÁTICO
	======================================== */

	useLayoutEffect(() => {
		if (scrollTargetIndex === null) return;

		latestQueryRef.current?.scrollIntoView({
			behavior: 'smooth',
			block: 'start',
		});
	}, [scrollTargetIndex]);

	/* ========================================
	   ENVIAR NOVA MENSAGEM
	======================================== */

	function handleNewQuery(message) {
		if (request) return;

		const question = message.trim();

		if (!question) return;

		const index = history.length;

		setHistory((current) => [
			...current,
			{
				question,
				answer: null,
				error: null,
			},
		]);

		setRequest({
			question,
			index,
		});

		setScrollTargetIndex(index);
	}

	/* ========================================
	   TENTAR NOVAMENTE
	======================================== */

	function handleRetry(index) {
		if (request) return;

		const item = history[index];

		if (!item) return;

		setHistory((current) =>
			current.map((entry, i) =>
				i === index ? { ...entry, answer: null, error: null } : entry,
			),
		);

		setRequest({
			question: item.question,
			index,
		});
	}

	/* ========================================
	   RENDERIZAÇÃO
	======================================== */

	if (!initialQuery) {
		return <Navigate to="/" replace />;
	}

	return (
		<div className="conversation-page">
			<main className="conversation-main">
				{history.map((item, index) => {
					const loading = request?.index === index;

					return (
						<div className="conversation-turn" key={index}>
							<UserQuery
								query={item.question}
								elementRef={index === history.length - 1 ? latestQueryRef : null}
							/>

							<div className="conversation-divider" />

							<section
								className="assistant-section"
								aria-live="polite"
								aria-busy={loading}
							>
								<AssistantHeading loading={loading} />

								{loading && <LoadingSkeleton />}

								{item.answer !== null && (
									<AssistantResponse response={item.answer} />
								)}

								{item.error && (
									<div className="conversation-error">
										<p>Não foi possível obter uma resposta: "{item.error}"</p>

										<button
											type="button"
											disabled={request !== null}
											onClick={() => handleRetry(index)}
										>
											Tentar novamente
										</button>
									</div>
								)}
							</section>
						</div>
					);
				})}
			</main>

			<ConversationInput loading={request !== null} onSubmit={handleNewQuery} />
		</div>
	);
}

export default ConversationPage;
