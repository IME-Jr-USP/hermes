import { Route, Routes } from 'react-router';
import './App.css';

import Header from './components/Header.jsx';
import AboutPage from './pages/AboutPage.jsx';
import ConversationPage from './pages/ConversationPage';
import HomePage from './pages/HomePage.jsx';

function App() {
	return (
		<>
			<Header />

			<Routes>
				<Route path="/" element={<HomePage />} />
				<Route path="/conversa" element={<ConversationPage />} />
				<Route path="/sobre" element={<AboutPage />} />
			</Routes>
		</>
	);
}

export default App;
