import { Plus } from 'lucide-react';
import logo from '../assets/logo.svg';
import './Header.css';

function Header() {
	return (
		<header className="header">
			<a href="#" className="header-brand">
				<img className="header-logo" src={logo} alt="" />
				<span className="header-name">Hermes</span>
			</a>

			<nav className="header-nav">
				<a href="/sobre">Sobre</a>
				<button type="button" id="header-newchat">
					<Plus size={17} strokeWidth={2} strokeLinecap="butt" strokeLinejoin="miter" />
					Nova conversa
				</button>
			</nav>
		</header>
	);
}

export default Header;
