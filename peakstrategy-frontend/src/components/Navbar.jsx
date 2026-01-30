import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Settings, LogOut, Menu, X } from 'lucide-react';
import { useState } from 'react';

const Navbar = () => {
  const { currentUser, logout } = useAuth();
  const [showDropdown, setShowDropdown] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = async () => {
    try {
      await logout();
      setShowDropdown(false);
      setMobileMenuOpen(false);
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  const handleSettings = () => {
    setShowDropdown(false);
    setMobileMenuOpen(false);
    window.location.href = '/settings';
  }

  return (
    <nav className="bg-white shadow-md w-full">
      <div className="flex items-center justify-between h-16 px-6">
        
        {/* LEFT: Brand */}
        <Link to="/" className="text-2xl font-bold text-gray-800">
          PeakStrategy
        </Link>

        {/* CENTER: Desktop Navigation */}
        <div className="hidden md:flex space-x-8">
          <Link to="/" className="nav-link">Dashboard</Link>
          <Link to="/research" className="nav-link">Research</Link>
          <Link to="/portfoliobuilder" className="nav-link">PortfolioBuilder</Link>
          <Link to="/chat" className="nav-link">Chat</Link>
        </div>

        {/* RIGHT: Auth / Settings */}
        <div className="flex items-center space-x-4">
          {currentUser ? (
            <div className="relative hidden md:block">
              <button
                onClick={() => setShowDropdown(!showDropdown)}
                className="flex items-center space-x-2 text-gray-600 hover:text-gray-900"
              >
                <Settings size={20} />
                <span>Settings</span>
              </button>

              {showDropdown && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg z-50">
                  <button 
                    onClick={handleSettings}
                    className="flex px-4 py-2 text-xs text-gray-500 border-b hover:bg-gray-100 w-full">
                    View settings
                  </button>
                  <button
                    onClick={handleLogout}
                    className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    <LogOut size={16} className="mr-2" />
                    Log Out
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="hidden md:flex space-x-3">
              <Link
                to="/signup"
                className="px-4 py-2 text-sm font-medium text-white bg-black rounded-md hover:bg-gray-800"
              >
                Sign Up
              </Link>
              <Link
                to="/login"
                className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900"
              >
                Sign In
              </Link>
            </div>
          )}

          {/* MOBILE MENU BUTTON */}
          <button
            className="md:hidden text-gray-700"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </div>

      {/* MOBILE DROPDOWN */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t bg-white shadow-sm">
          <div className="flex flex-col space-y-2 px-6 py-4">
            <Link to="/" onClick={() => setMobileMenuOpen(false)} className="mobile-link">
              Dashboard
            </Link>
            <Link to="/research" onClick={() => setMobileMenuOpen(false)} className="mobile-link">
              Research
            </Link>
            <Link to="/portfoliobuilder" onClick={() => setMobileMenuOpen(false)} className="mobile-link">
              PortfolioBuilder
            </Link>
            <Link to="/chat" onClick={() => setMobileMenuOpen(false)} className="mobile-link">
              Chat
            </Link>

            <div className="border-t pt-3">
              {currentUser ? (
                <button
                  onClick={handleLogout}
                  className="flex items-center text-sm text-red-600 hover:text-red-700"
                >
                  <LogOut size={16} className="mr-2" />
                  Log Out
                </button>
              ) : (
                <>
                  <Link to="/signup" className="mobile-link">Sign Up</Link>
                  <Link to="/login" className="mobile-link">Sign In</Link>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navbar;

