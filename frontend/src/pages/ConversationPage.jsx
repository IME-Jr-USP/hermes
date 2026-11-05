import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { Navigate, useLocation } from 'react-router';

import { ArrowDown, ArrowUp, Hourglass } from 'lucide-react';

import Skeleton, { SkeletonTheme } from 'react-loading-skeleton';
import 'react-loading-skeleton/dist/skeleton.css';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

import './ConversationPage.css';

/* -------------------------------------------------------------------------- */
/*                                     API                                    */
/* -------------------------------------------------------------------------- */

const API_URL = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000').replace(/\/+$/, '');
const pendingRequests = new Map(); // evitar chamadas duplicadas

function getResponse(query, conversaId, requestId) {
	if (!query.trim()) {
		throw new Error('Consulta vazia.');
	}

	if (pendingRequests.has(requestId)) {
		return pendingRequests.get(requestId);
	}

	const promise = fetch(`${API_URL}/api/chat`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
		},
		body: JSON.stringify({
			mensagem: query,
			conversa_id: conversaId,
		}),
	})
		.then(async (response) => {
			const data = await response.json().catch(() => null);

			if (!response.ok) {
				throw new Error(data?.detail ?? 'Não foi possível obter uma resposta do Hermes.');
			}

			if (typeof data?.resposta !== 'string') {
				throw new Error('O servidor retornou uma resposta inválida.');
			}

			return data.resposta;
		})
		.finally(() => {
			pendingRequests.delete(requestId);
		});

	pendingRequests.set(requestId, promise);

	return promise;
}

/* -------------------------------------------------------------------------- */
/*                                 Componentes                                */
/* -------------------------------------------------------------------------- */

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
			<ReactMarkdown
				remarkPlugins={[remarkGfm]}
				components={{
					a: ({ href, children, ...props }) => (
						<a href={href} target="_blank" rel="noopener noreferrer" {...props}>
							{children}
						</a>
					),
				}}
			>
				{response}
			</ReactMarkdown>
		</div>
	);
}

function ConversationInput({ loading, onSubmit, showScrollToBottom, onScrollToBottom }) {
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
			{showScrollToBottom && (
				<button
					className="scroll-to-bottom"
					type="button"
					aria-label="Ir para o fim da conversa"
					onClick={onScrollToBottom}
				>
					<ArrowDown size={20} strokeWidth={2.2} />
				</button>
			)}
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

function ConversationPage() {
	const location = useLocation();
	const initialQuery = location.state?.query?.trim() ?? '';
	const conversationMainRef = useRef(null);
	const latestQueryRef = useRef(null);
	const [scrollTargetIndex, setScrollTargetIndex] = useState(null);

	const [conversaId] = useState(() => crypto.randomUUID());
	const [history, setHistory] = useState(() =>
		initialQuery ? [{ question: initialQuery, answer: null, error: null }] : [],
	);
	const [request, setRequest] = useState(() =>
		initialQuery
			? {
					question: initialQuery,
					index: 0,
					id: crypto.randomUUID(),
				}
			: null,
	);

	useEffect(() => {
		if (!request) return;

		let cancelled = false;

		// Carregar resposta do agente
		async function loadResponse() {
			try {
				const result = await getResponse(request.question, conversaId, request.id);

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

		loadResponse();

		return () => {
			cancelled = true;
		};
	}, [request, conversaId]);

	// Scroll automático
	useLayoutEffect(() => {
		if (scrollTargetIndex === null) return;

		latestQueryRef.current?.scrollIntoView({
			behavior: 'smooth',
			block: 'start',
		});
	}, [scrollTargetIndex]);

	// Botão de Scroll to Bottom
	const [showScrollToBottom, setShowScrollToBottom] = useState(false);

	useEffect(() => {
		function updateScrollButton() {
			const pageHeight = Math.max(
				document.documentElement.scrollHeight,
				document.body.scrollHeight,
			);

			const distanceFromBottom = pageHeight - window.innerHeight - window.scrollY;
			setShowScrollToBottom(distanceFromBottom > 300);
		}

		updateScrollButton();

		window.addEventListener('scroll', updateScrollButton, { passive: true });
		window.addEventListener('resize', updateScrollButton);

		const resizeObserver = new ResizeObserver(updateScrollButton);

		if (conversationMainRef.current) {
			resizeObserver.observe(conversationMainRef.current);
		}

		return () => {
			window.removeEventListener('scroll', updateScrollButton);
			window.removeEventListener('resize', updateScrollButton);
			resizeObserver.disconnect();
		};
	}, []);

	function handleScrollToBottom() {
		const pageHeight = Math.max(
			document.documentElement.scrollHeight,
			document.body.scrollHeight,
		);

		window.scrollTo({
			top: pageHeight,
			behavior: 'smooth',
		});
	}

	// Enviar nova mensagem
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
			id: crypto.randomUUID(),
		});

		setScrollTargetIndex(index);
	}

	// Tentar novamente
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
			id: crypto.randomUUID(),
		});
	}

	// Renderização
	if (!initialQuery) {
		return <Navigate to="/" replace />;
	}

	return (
		<div className="conversation-page">
			<main className="conversation-main" ref={conversationMainRef}>
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
			<ConversationInput
				loading={request !== null}
				onSubmit={handleNewQuery}
				showScrollToBottom={showScrollToBottom}
				onScrollToBottom={handleScrollToBottom}
			/>{' '}
		</div>
	);
}

export default ConversationPage;
