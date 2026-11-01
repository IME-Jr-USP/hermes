import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { Navigate, useLocation } from 'react-router';

import { ArrowDown, ArrowUp, Hourglass } from 'lucide-react';

import Skeleton, { SkeletonTheme } from 'react-loading-skeleton';
import 'react-loading-skeleton/dist/skeleton.css';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

import './ConversationPage.css';

/* ========================================
   DEMO
======================================== */

const DEMO_RESPONSE = `
# Guia completo de disciplinas de IA

Encontrei **3 disciplinas** que combinam com os seus interesses em *inteligência artificial* e ~~programação básica~~ aprendizado de máquina. Todas têm atividades no período da tarde e podem entrar na sua grade. Veja também o [catálogo de disciplinas](https://example.com/catalogo) para mais detalhes, ou acesse direto https://example.com/matricula.

Este parágrafo tem uma segunda linha logo abaixo, separada por quebra simples.
Ela deve aparecer na linha seguinte, dentro do mesmo parágrafo.

---

## Disciplinas recomendadas

### 1. Introdução ao Aprendizado de Máquina

#### IME — Instituto de Matemática e Estatística

| Informação | Detalhes |
| --- | --- |
| Código | MAC0460 |
| Créditos | 4 créditos-aula |
| Horário | Segundas e quartas, 14h–15h40 |
| Pré-requisitos | MAC0110 e MAE0121 |

Excelente opção para aprofundar seus conhecimentos em **modelos estatísticos**, *algoritmos de aprendizado* e programação em Python.

- **Área:** Inteligência Artificial
- **Nível:** Intermediário
- **Avaliação:**
  - Duas provas escritas
  - Listas de exercícios semanais
    - Entrega pelo sistema da disciplina
    - Resolução individual
  - Projeto final em dupla

### 2. Redes Neurais e Aprendizado Profundo

#### IME — Instituto de Matemática e Estatística

| Informação | Detalhes | Observação |
| --- | --- | --- |
| Código | MAC5921 | Pós-graduação |
| Créditos | 6 créditos-aula | Com trabalho |
| Horário | Terças e quintas, 14h–15h40 | Sala 232 |

Esta disciplina exige boa base em álgebra linear. Os passos recomendados para se preparar são:

1. Revisar álgebra linear e cálculo multivariável
2. Praticar Python com NumPy
   1. Operações com matrizes
   2. Gradiente e derivadas parciais
3. Ler o capítulo inicial do livro-texto
4. Conversar com o professor antes da matrícula

> **Dica:** disciplinas de pós-graduação podem ser cursadas como aluno especial, mas as vagas são limitadas e dependem de aprovação do docente.
>
> > Confirme sempre no JúpiterWeb antes da matrícula.

### 3. Visão Computacional

#### IME — Instituto de Matemática e Estatística

Veja um exemplo de como processar imagens com a biblioteca \`OpenCV\`, usada ao longo do curso:

\`\`\`python
import cv2

imagem = cv2.imread("foto.jpg")
cinza = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
bordas = cv2.Canny(cinza, 100, 200)

cv2.imwrite("bordas.png", bordas)
print(f"Dimensões: {bordas.shape}")
\`\`\`

Para instalar a dependência, use o terminal:

\`\`\`bash
pip install opencv-python numpy
\`\`\`

---

## Exemplos de imagens

Imagem **grande e panorâmica** (deve ser limitada pela largura máxima):

![Imagem panorâmica de exemplo](https://placehold.co/1600x700/png?text=Panoramica+1600x700)

Imagem **vertical** (deve ser limitada pela altura máxima):

![Imagem vertical de exemplo](https://placehold.co/600x1200/png?text=Vertical+600x1200)

Imagem **pequena** (deve manter o tamanho natural, centralizada):

![Imagem pequena de exemplo](https://placehold.co/160x160/png?text=160x160)

---

## Checklist para a matrícula

- [x] Verificar pré-requisitos no JúpiterWeb
- [x] Conferir conflitos de horário
- [ ] Falar com a coordenação sobre vagas
	- [ ] Item 1
	- [ ] Item 2
		- Subitem 1
		- Subitem 2
		- Subitem 3
			- [ ] Subtarefa 1
		- Subitem 4
- [ ] Confirmar a matrícula dentro do prazo

## Resumo comparativo

| Disciplina | Nível | Créditos | Dificuldade |
| :--- | :---: | ---: | :---: |
| Introdução ao Aprendizado de Máquina | Graduação | 4 | Média |
| Redes Neurais e Aprendizado Profundo | Pós-graduação | 6 | Alta |
| Visão Computacional | Graduação | 4 | Média |

Se quiser, posso montar uma **grade semanal** com essas disciplinas ou buscar *alternativas* em outros institutos. Use \`Ctrl + F\` na página do catálogo para filtrar por código.
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

/* ========================================
   CONVERSATION INPUT
======================================== */

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

/* ========================================
   CONVERSATION PAGE
======================================== */

function ConversationPage() {
	const location = useLocation();
	const initialQuery = location.state?.query?.trim() ?? '';
	const conversationMainRef = useRef(null);

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
	   BOTÃO SCROLL TO BOTTOM
	======================================== */
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
