import { ArrowRight, BookOpen, ChevronRight } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

import './HomePage.css';

const exampleQueries = [
	'Disciplinas introdutórias de Filosofia da Ciência abertas a outros cursos',
	'Optativas sobre Aprendizado de Máquina e Dados no IME ou na Poli',
	'Tópicos de Economia e Políticas Públicas para não-economistas',
];

function HomePage({ onSearch }) {
	const [query, setQuery] = useState('');
	const textareaRef = useRef(null);

	function handleSubmit(event) {
		event.preventDefault();

		const search = query.trim();

		if (!search) return;

		onSearch?.(search);
	}

	useEffect(() => {
		const textarea = textareaRef.current;

		if (!textarea) return;

		textarea.style.height = 'auto';
		textarea.style.height = `${textarea.scrollHeight}px`;
	}, [query]);

	return (
		<div className="home-page">
			<main className="home-main">
				<section className="home-hero">
					<div className="home-meta">
						<span className="home-meta-dot" />
						+8.400 disciplinas catalogadas · Atualizado 1º semestre 2026
					</div>

					<h1 className="home-title">
						O que você gostaria de cursar neste semestre na USP?
					</h1>

					<p className="home-description">
						Busque por temas de interesse, ementas, professores ou horários entre todos
						os institutos da universidade.
					</p>
				</section>

				<form className="search-form" onSubmit={handleSubmit}>
					<textarea
						ref={textareaRef}
						className="search-input"
						value={query}
						onChange={(event) => setQuery(event.target.value)}
						placeholder="Ex: Procuro optativas livres sobre Inteligência Artificial ou Ética na USP às quintas-feiras à noite..."
						rows={2}
					/>

					<div className="search-form-bottom">
						<div className="search-mode">
							<BookOpen size={14} strokeWidth={1.5} />
							<span>Linguagem natural sobre ementas</span>
						</div>

						<button
							className="search-submit"
							type="submit"
							aria-label="Enviar consulta"
							disabled={!query.trim()}
						>
							<ArrowRight
								className="search-submit-icon"
								size={19}
								strokeWidth={1.8}
							/>
						</button>
					</div>
				</form>

				<section className="example-queries">
					<div className="example-queries-header">
						<h2>Exemplos de consulta</h2>
						<span>Clique para testar</span>
					</div>

					<div className="example-queries-list">
						{exampleQueries.map((example) => (
							<button
								className="example-query"
								type="button"
								onClick={() => {
									setQuery(example);
									textareaRef.current?.focus();
								}}
							>
								<span>{example}</span>
								<ChevronRight size={16} />
							</button>
						))}
					</div>
				</section>

				<div className="home-disclaimer">
					<p>
						Respostas baseadas nas ementas e catálogos oficiais de graduação do
						JúpiterWeb.
					</p>
					<p>
						Para inscrições formais e trancamentos, consulte sempre o sistema oficial.
					</p>
				</div>
			</main>

			<footer className="home-footer">
				<p>Hermes — Assistente de Disciplinas USP · Dados abertos do JúpiterWeb</p>
			</footer>
		</div>
	);
}

export default HomePage;
