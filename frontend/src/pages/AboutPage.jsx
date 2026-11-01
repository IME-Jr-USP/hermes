import './AboutPage.css';

function AboutPage() {
	return (
		<div className="about-page">
			<main className="about-main">
				<section className="about-hero">
					<div className="about-meta">
						<span className="about-meta-dot"></span>
						Sobre o Projeto · Iniciativa Acadêmica Independente
					</div>
					<h1 className="about-title">
						Um guia de caminhos para a grade curricular da USP
					</h1>
					<p className="about-description">
						O Hermes nasceu para transformar a busca textual por ementas em uma
						experiência de descoberta interdisciplinar fluida, contextualizada e
						precisa.
					</p>
					<div className="about-dbinfo-wrapper">
						<div className="about-dbinfo">
							<span className="about-dbinfo-title">Cobertura Institucional</span>
							<span className="about-dbinfo-data">
								<span className="about-dbinfo-value">42</span>
								<span className="about-dbinfo-subtitle">unidades e institutos</span>
							</span>
							<span className="about-dbinfo-description">
								Integrados na capital e campi do interior da USP
							</span>
						</div>
						<div className="about-dbinfo">
							<span className="about-dbinfo-title">Ementário Ativo</span>
							<span className="about-dbinfo-data">
								<span className="about-dbinfo-value">7.800</span>
								<span className="about-dbinfo-subtitle">disciplinas indexadas</span>
							</span>
							<span className="about-dbinfo-description">
								Ementas, objetivos pedagógicos e créditos
							</span>
						</div>
					</div>
				</section>

				<section className="about-section">
					<h2>Por que o Hermes existe?</h2>
					<p>
						Semestralmente, milhares de estudantes de graduação da Universidade de São
						Paulo encaram o desafio da consolidação de matrícula através do JúpiterWeb.
						Embora seja o repositório oficial de registros acadêmicos, a busca do
						sistema tradicional baseia-se primordialmente em códigos rígidos de
						departamento ou termos literais exatos.
					</p>
					<p>
						Essa barreira dificulta a navegação entre diferentes faculdades e
						institutos. Estudantes da Poli que procuram noções de epistemologia na
						FFLCH, ou discentes do IME interessados em economia comportamental na FEA ou
						design de produto na FAU, frequentemente não encontram essas matérias sem
						conhecer previamente a sigla exata de cada departamento.
					</p>
					<p>
						A missão do <b>Hermes</b> é conectar interesses intelectuais a matérias
						reais, aproximando os estudantes de saberes fora do seu departamento de
						origem através de linguagem natural — estimulando a formação plural e
						interdisciplinar que define a excelência pública da universidade.
					</p>
				</section>
				<section className="about-section">
					<span className="about-section-meta">Metodologia</span>
					<h2>Como o assistente compreende sua busca</h2>

					<div className="about-subsection">
						<h3>Ingestão contínua de ementas oficiais</h3>
						<p>
							Indexação periódica dos catálogos públicos abertos da graduação,
							cobrindo objetivos pedagógicos, programas de aula, referências
							bibliográficas e requisitos de créditos aula e trabalho.
						</p>
					</div>
					<div className="about-subsection">
						<h3>Compreensão semântica em linguagem natural</h3>
						<p>
							Em vez de palavras-chave exatas, o assistente correlaciona interesses
							temáticos, preferências de turno e anseios de formação aos conteúdos
							programáticos homologados pelas congregações da USP.{' '}
						</p>
					</div>
					<div className="about-subsection">
						<h3>Síntese editorial e transparência ementária</h3>
						<p>
							Cada recomendação preserva códigos originais, horários típicos e
							justificativas transparentes, mantendo sempre o vínculo direto para a
							ementa oficial no catálogo da universidade.
						</p>
					</div>
				</section>
				<section className="about-section">
					<span className="about-section-meta">Exemplo Prático</span>
					<h2>Como um estudante utiliza o Hermes</h2>

					<p>
						O estudante formula objetivos acadêmicos com o contexto do seu percurso
						individual, sem necessidade de memorizar previamente siglas regimentais ou
						códigos departamentais:
					</p>
				</section>
				<section className="about-disclaimer">
					<h2>Isenção de Responsabilidade & Verificação</h2>
					<p>
						O Hermes é uma ferramenta acadêmica independente voltada à orientação e
						experimentação discente,{' '}
						<b>sem vínculo formal com a Pró-Reitoria de Graduação (PRG)</b>. Matrículas,
						requerimentos de vagas, trancamentos e validações de equivalência devem ser
						realizados e confirmados sempre através do sistema oficial JúpiterWeb e
						junto à Seção de Alunos de sua unidade.
					</p>
				</section>
			</main>
		</div>
	);
}

export default AboutPage;
