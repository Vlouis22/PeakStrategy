import { Routes, Route } from 'react-router-dom';
import Dashboard from '../pages/Dashboard';
import Research from '../pages/Research';
import PortfolioBuilder from '../pages/PortfolioBuilder';
import Chat from '../pages/Chat';
import Signup from '../pages/Signup';
import Login from '../pages/Login';
import Settings from '../pages/Settings';

const AppRoutes = () => {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/research" element={<Research />} />
      <Route path="/portfoliobuilder" element={<PortfolioBuilder />} />
      <Route path="/chat" element={<Chat />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/login" element={<Login />} />
      <Route path="/settings" element={<Settings />} />
    </Routes>
  );
};

export default AppRoutes;