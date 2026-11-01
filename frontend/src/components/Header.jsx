import { Plus } from 'lucide-react';
import { useNavigate } from 'react-router';
import logo from '../assets/logo.svg';
import './Header.css';

function Header() {
	const navigate = useNavigate();

	return (
		<header className="header">
			<div className="header-brand">
				<img className="header-logo" src={logo} alt="" />
				<span className="header-name">Hermes</span>
			</div>

			<nav className="header-nav">
				<a href="/sobre">Sobre</a>
				<button type="button" id="header-newchat" onClick={() => navigate('/')}>
					<Plus size={17} strokeWidth={2} strokeLinecap="butt" strokeLinejoin="miter" />
					Nova conversa
				</button>
			</nav>
		</header>
	);
}

export default Header;
