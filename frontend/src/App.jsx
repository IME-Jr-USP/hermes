import { Route, Routes } from 'react-router';
import './App.css';

import Header from './components/Header.jsx';
import ConversationPage from './pages/ConversationPage';
import HomePage from './pages/HomePage.jsx';

function App() {
	return (
		<>
			<Header />

			<Routes>
				<Route path="/" element={<HomePage />} />
				<Route path="/conversa" element={<ConversationPage />} />
			</Routes>
		</>
	);
}

export default App;
