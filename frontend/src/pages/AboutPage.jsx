import './AboutPage.css';

function AboutPage() {
	return (
		<div className="about-page">
			<main className="about-main">
				<h1>Encontre disciplinas que combinam com seus interesses.</h1>
				<p>
					O Hermes é um assistente que ajuda estudantes da USP a descobrir e explorar
					disciplinas de graduação. Basta descrever o que você gostaria de estudar ou seus
					interesses para encontrar disciplinas relacionadas.
				</p>

				<h1>Como funciona?</h1>
				<p>
					O Hermes reúne informações do catálogo de disciplinas da USP e utiliza busca
					semântica para identificar opções relevantes para o que você procura. Assim,
					você pode descobrir disciplinas mesmo sem conhecer seus nomes ou códigos.
				</p>

				<h1>Uma observação</h1>
				<p>
					As informações apresentadas têm caráter orientativo. Antes de tomar decisões
					sobre matrícula, consulte os canais oficiais da USP para confirmar oferecimento,
					horários, requisitos e demais informações.
				</p>
			</main>
		</div>
	);
}

export default AboutPage;
