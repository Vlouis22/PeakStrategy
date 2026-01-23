import { useState, useEffect, useCallback, useMemo } from 'react';
import { useAuth } from '../contexts/AuthContext';
import PortfolioForm from '../components/PortfolioForm.jsx';
import PortfolioAllocationChart from '../components/PortfolioAllocationChart.jsx';
import { portfolioApi } from '../services/portfolioApi';
import PortfolioProjection from '../components/PortfolioProjection.jsx';
import PriceChangesTable from '../components/PriceChangesTable.jsx';

const Dashboard = () => {
  const { currentUser, getProfile, loading } = useAuth();
  const [displayName, setDisplayName] = useState('');
  const [portfolios, setPortfolios] = useState([]);
  const [selectedPortfolio, setSelectedPortfolio] = useState(null);
  const [showPortfolioForm, setShowPortfolioForm] = useState(false);
  const [isEditingPortfolio, setIsEditingPortfolio] = useState(false);
  const [profileLoading, setProfileLoading] = useState(false);
  const [portfoliosLoading, setPortfoliosLoading] = useState(true);
  const [performanceLoading, setPerformanceLoading] = useState(false);
  const [performanceError, setPerformanceError] = useState('');
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [overallStats, setOverallStats] = useState({
    totalCostBasis: 0,
    currentValue: 0,
    totalChange: 0,
    totalChangePercent: 0
  });
  const [individualPrices, setIndividualPrices] = useState({});

  // Auto-dismiss success messages after 5 seconds
  useEffect(() => {
    if (successMessage) {
      const timer = setTimeout(() => {
        setSuccessMessage('');
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [successMessage]);

  // Normalize portfolio data to ensure consistent property names
  const normalizePortfolio = useCallback((portfolio) => {
    return {
      ...portfolio,
      id: portfolio.id,
      name: portfolio.name || '',
      createdAt: portfolio.createdAt,
      holdings: portfolio.holdings || [],
      totalCostBasis: portfolio.total_cost_basis || portfolio.totalCostBasis || 0,
      currentValue: portfolio.current_value || portfolio.currentValue || 0,
      totalChange: portfolio.total_change || portfolio.totalChange || 0,
      totalChangePercent: portfolio.total_change_percent || portfolio.totalChangePercent || 0
    };
  }, []);

  // Fetch user profile and portfolios on component mount
  useEffect(() => {
    const fetchData = async () => {
      if (!loading && currentUser) {
        try {
          setProfileLoading(true);
          setPortfoliosLoading(true);
          
          // Fetch user profile
          const profile = await getProfile();
          setDisplayName(profile.display_name || currentUser.displayName || 'User');
          
          // Fetch user portfolios and normalize data
          const portfolioData = await portfolioApi.getPortfolios();
          const normalizedPortfolios = (portfolioData.portfolios || []).map(normalizePortfolio);
          setPortfolios(normalizedPortfolios);
          
        } catch (error) {
          console.error("Failed to fetch data:", error);
          setDisplayName('User');
          setError('Failed to load portfolios. Please try again.');
        } finally {
          setProfileLoading(false);
          setPortfoliosLoading(false);
        }
      }
    };
    
    fetchData();
  }, [currentUser, getProfile, loading, normalizePortfolio]);

  // Fetch portfolio performances and individual prices
  useEffect(() => {
    const fetchPerformance = async () => {
      if (!currentUser || portfolios.length === 0) return;
      
      try {
        setPerformanceLoading(true);
        setPerformanceError('');
        const performanceData = await portfolioApi.getPortfoliosPerformance();
        
        if (performanceData.success) {
          // Store individual prices
          if (performanceData.individual_prices) {
            setIndividualPrices(performanceData.individual_prices);
          }
          
          // Update portfolios with performance data
          const updatedPortfolios = portfolios.map(portfolio => {
            const performance = performanceData.portfolios?.find(p => p.id === portfolio.id);
            if (performance) {
              return {
                ...portfolio,
                currentValue: performance.current_value || performance.currentValue || portfolio.currentValue || 0,
                totalChange: performance.total_change || performance.totalChange || portfolio.totalChange || 0,
                totalChangePercent: performance.total_change_percent || performance.totalChangePercent || portfolio.totalChangePercent || 0
              };
            }
            return portfolio;
          });
          
          setPortfolios(updatedPortfolios);
          
          // Update overall stats
          if (performanceData.overall) {
            setOverallStats({
              totalCostBasis: performanceData.overall.total_cost_basis || performanceData.overall.totalCostBasis || 0,
              currentValue: performanceData.overall.current_value || performanceData.overall.currentValue || 0,
              totalChange: performanceData.overall.total_change || performanceData.overall.totalChange || 0,
              totalChangePercent: performanceData.overall.total_change_percent || performanceData.overall.totalChangePercent || 0
            });
          }
        } else {
          // Handle backend returned success: false
          setPerformanceError(performanceData.error || 'Failed to fetch performance data. Please try again later.');
        }
      } catch (error) {
        console.error("Failed to fetch performance:", error);
        setPerformanceError('Unable to load current stock prices. Your portfolio totals are based on cost basis only. Please check your internet connection or try again later.');
      } finally {
        setPerformanceLoading(false);
      }
    };
    
    // Add a small delay to prevent race conditions
    const timer = setTimeout(() => {
      if (portfolios.length > 0) {
        fetchPerformance();
      }
    }, 100);
    
    return () => clearTimeout(timer);
  }, [currentUser, portfolios.length]);

  // Refresh portfolios after create/update
  const refreshPortfolios = useCallback(async () => {
    try {
      setPortfoliosLoading(true);
      const portfolioData = await portfolioApi.getPortfolios();
      const normalizedPortfolios = (portfolioData.portfolios || []).map(normalizePortfolio);
      setPortfolios(normalizedPortfolios);
    } catch (error) {
      console.error("Failed to refresh portfolios:", error);
      setError('Failed to refresh portfolios. Please try again.');
    } finally {
      setPortfoliosLoading(false);
    }
  }, [normalizePortfolio]);

  // Handle create portfolio button click
  const handleCreatePortfolioClick = useCallback(() => {
    if (portfolios.length >= 3) {
      setError('You can only have a maximum of 3 portfolios');
      return;
    }
    setSelectedPortfolio(null);
    setIsEditingPortfolio(false);
    setShowPortfolioForm(true);
  }, [portfolios.length]);

  // Handle update portfolio button click
  const handleUpdatePortfolioClick = useCallback((portfolio) => {
    setSelectedPortfolio(portfolio);
    setIsEditingPortfolio(true);
    setShowPortfolioForm(true);
  }, []);

  // Handle successful portfolio creation/update
  const handlePortfolioSuccess = useCallback(async (response) => {
    await refreshPortfolios();
    setShowPortfolioForm(false);
    setSelectedPortfolio(null);
    setIsEditingPortfolio(false);
    setError('');
    setSuccessMessage(isEditingPortfolio ? 'Portfolio updated successfully!' : 'Portfolio created successfully!');
  }, [isEditingPortfolio, refreshPortfolios]);

  // Handle portfolio form cancel
  const handlePortfolioCancel = useCallback(() => {
    setShowPortfolioForm(false);
    setSelectedPortfolio(null);
    setIsEditingPortfolio(false);
    setError('');
  }, []);

  // Handle portfolio delete
  const handleDeletePortfolio = useCallback(async (portfolioId) => {
    if (window.confirm('Are you sure you want to delete this portfolio? This action cannot be undone.')) {
      try {
        await portfolioApi.deletePortfolio(portfolioId);
        await refreshPortfolios();
        setSuccessMessage('Portfolio deleted successfully!');
      } catch (error) {
        console.error('Failed to delete portfolio:', error);
        setError('Failed to delete portfolio. Please try again.');
      }
    }
  }, [refreshPortfolios]);

  // Format date for display
  const formatDate = useCallback((date) => {
    try {
      if (date?.seconds) {
        return new Date(date.seconds * 1000).toLocaleDateString();
      }
      return new Date(date).toLocaleDateString();
    } catch (error) {
      return 'Unknown date';
    }
  }, []);

  // Determine portfolio grid layout based on portfolio count
  const portfolioGridClasses = useMemo(() => {
    const count = portfolios.length;
    if (count === 1) return "flex justify-center";
    if (count === 2) return "grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto";
    return "grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6";
  }, [portfolios.length]);

  // Determine portfolio card width based on portfolio count
  const portfolioCardClasses = useMemo(() => {
    const count = portfolios.length;
    if (count === 1) return "w-full max-w-2xl";
    if (count === 2) return "w-full";
    return "w-full";
  }, [portfolios.length]);

  // Loading state
  if (loading || profileLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-lg">Loading your dashboard...</div>
      </div>
    );
  }

  // User not logged in
  if (!currentUser) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">No profile found</h1>
          <p className="text-gray-600">Please sign in to access your dashboard.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white p-4 sm:p-6 lg:p-8">
      {/* Error Messages */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center">
            <svg className="w-5 h-5 text-red-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.998-.833-2.732 0L4.732 16.5c-.77.833.192 2.5 1.732 2.5" />
            </svg>
            <span className="text-red-700">{error}</span>
            <button
              onClick={() => setError('')}
              className="ml-auto text-red-600 hover:text-red-800"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}

      {/* Success Messages */}
      {successMessage && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center">
            <svg className="w-5 h-5 text-green-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="text-green-700">{successMessage}</span>
            <button
              onClick={() => setSuccessMessage('')}
              className="ml-auto text-green-600 hover:text-green-800"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}

      {/* Performance Error */}
      {performanceError && !performanceLoading && (
        <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="flex items-start">
            <svg className="w-5 h-5 text-yellow-500 mr-2 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.998-.833-2.732 0L4.732 16.5c-.77.833.192 2.5 1.732 2.5" />
            </svg>
            <div className="flex-1">
              <p className="text-yellow-700 font-medium">Performance Data Unavailable</p>
              <p className="text-yellow-600 text-sm mt-1">{performanceError}</p>
              <p className="text-yellow-600 text-sm mt-1">
                Displayed values are based on cost basis only.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Dashboard Header */}
      <div className="mb-8">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 mb-6">
          <div className="text-center w-full">
            <h1 className="text-3xl sm:text-4xl font-bold text-black">
              Welcome back, {displayName}!
            </h1>
            <p className="mt-2 text-gray-600">
              Manage your investment portfolios
            </p>
          </div>
        </div>
        
        {/* Stats Summary */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          {[
            { 
              label: 'Total Portfolios', 
              value: `${portfolios.length}/3`, 
              icon: 'portfolio', 
              color: 'text-black' 
            },
            { 
              label: 'Cost Basis', 
              value: `$${overallStats.totalCostBasis.toFixed(2)}`, 
              icon: 'cost', 
              color: 'text-black' 
            },
            { 
              label: 'Current Value', 
              value: performanceError ? '--' : `$${overallStats.currentValue.toFixed(2)}`,
              subtext: performanceError ? 'Live prices unavailable' : '',
              icon: 'value',
              color: 'text-black'
            },
            { 
              label: 'Total Return', 
              value: performanceError ? '--' : `${overallStats.totalChangePercent.toFixed(2)}%`,
              subtext: performanceError ? 'Live prices unavailable' : `$${overallStats.totalChange.toFixed(2)}`,
              icon: 'return',
              color: overallStats.totalChangePercent >= 0 ? 'text-green-600' : 'text-red-600'
            }
          ].map((stat, index) => (
            <div key={index} className="bg-white border border-gray-200 rounded-xl p-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 mb-1">{stat.label}</p>
                  <div className="flex items-center">
                    <p className={`text-2xl font-bold ${stat.color}`}>
                      {stat.value}
                    </p>
                    {performanceLoading && stat.label !== 'Total Portfolios' && stat.label !== 'Cost Basis' && (
                      <svg className="animate-spin h-4 w-4 ml-2 text-gray-400" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                    )}
                  </div>
                  {stat.subtext && (
                    <p className="text-xs text-gray-500 mt-1">{stat.subtext}</p>
                  )}
                </div>
                <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                  {stat.icon === 'portfolio' && (
                    <svg className="w-5 h-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                    </svg>
                  )}
                  {stat.icon === 'cost' && (
                    <svg className="w-5 h-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  )}
                  {stat.icon === 'value' && (
                    <svg className="w-5 h-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                    </svg>
                  )}
                  {stat.icon === 'return' && (
                    <svg className="w-5 h-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Main Content Area */}
      {showPortfolioForm ? (
        <PortfolioForm
          portfolio={selectedPortfolio}
          isEditing={isEditingPortfolio}
          onSuccess={handlePortfolioSuccess}
          onCancel={handlePortfolioCancel}
        />
      ) : portfoliosLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="text-lg text-gray-600">Loading portfolios...</div>
        </div>
      ) : portfolios.length === 0 ? (
        <div className="bg-white border-2 border-dashed border-gray-300 rounded-2xl p-8 sm:p-12 text-center">
          <div className="w-24 h-24 mx-auto mb-6 bg-gray-100 rounded-full flex items-center justify-center">
            <svg className="w-12 h-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-black mb-3">No Portfolios Found</h2>
          <p className="text-gray-600 mb-8 max-w-md mx-auto">
            You haven't created any portfolios yet. Start building your investment portfolio by creating your first one.
          </p>
          <button
            onClick={handleCreatePortfolioClick}
            className="px-8 py-3 bg-black text-white font-medium rounded-lg hover:bg-gray-800 transition-colors inline-flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Create Your First Portfolio
          </button>
        </div>
      ) : (
        <div>
          {/* Performance Loading State */}
          {performanceLoading && (
            <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-center">
                <svg className="animate-spin h-5 w-5 text-blue-500 mr-2" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                <span className="text-blue-700">Loading current market prices...</span>
              </div>
            </div>
          )}

          {/* Portfolio Grid */}
          <div className={portfolioGridClasses}>
            {portfolios.map((portfolio) => (
              <div key={portfolio.id} className={`${portfolioCardClasses} mb-6`}>
                <div className="bg-white border border-gray-200 rounded-xl p-6 hover:shadow-lg transition-all duration-300 h-full">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="text-xl font-bold text-black mb-1">{portfolio.name}</h3>
                      <p className="text-sm text-gray-600">
                        Created {formatDate(portfolio.createdAt)}
                      </p>
                    </div>
                    <button
                      onClick={() => handleUpdatePortfolioClick(portfolio)}
                      className="text-black hover:text-gray-700 transition-colors"
                      title="Edit portfolio"
                    >
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                    </button>
                  </div>
                  
                  <div className="space-y-4 mb-6">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Holdings</span>
                      <span className="font-medium text-black">{portfolio.holdings?.length || 0}</span>
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Cost Basis</span>
                      <span className="font-medium text-black">
                        ${(portfolio.totalCostBasis || 0).toFixed(2)}
                      </span>
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Current Value</span>
                      <div className="text-right">
                        <div className="flex items-center justify-end">
                          <span className={`font-medium ${performanceError ? 'text-gray-500' : 'text-black'}`}>
                            {performanceError ? 'Market data unavailable' : `$${(portfolio.currentValue || 0).toFixed(2)}`}
                          </span>
                          {performanceLoading && !performanceError && (
                            <svg className="animate-spin h-3 w-3 ml-1 text-gray-400" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                            </svg>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Total Return</span>
                      <div className="text-right">
                        {performanceError ? (
                          <span className="text-sm text-gray-500">Live prices required</span>
                        ) : (
                          <>
                            <div className={`font-semibold ${(portfolio.totalChange || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                              ${(portfolio.totalChange || 0).toFixed(2)}
                            </div>
                            <div className={`text-sm ${(portfolio.totalChangePercent || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                              {(portfolio.totalChangePercent || 0).toFixed(2)}%
                            </div>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex gap-3 pt-4 border-t border-gray-100">
                    <button
                      onClick={() => handleUpdatePortfolioClick(portfolio)}
                      className="flex-1 py-2.5 border border-black text-black font-medium rounded-lg hover:bg-black hover:text-white transition-colors duration-200"
                    >
                      Edit {portfolio.name}
                    </button>
                    <button
                      onClick={() => handleDeletePortfolio(portfolio.id)}
                      className="px-4 py-2.5 border border-red-600 text-red-600 font-medium rounded-lg hover:bg-red-50 transition-colors duration-200"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            ))}

            {/* Create New Portfolio Card */}
            {portfolios.length < 3 && (
              <div className={`${portfolios.length === 1 ? 'w-full max-w-2xl mb-4' : portfolios.length === 2 ? 'md:col-span-2 mb-10' : 'lg:col-span-2 xl:col-span-3 mb-4'}`}>
                <div className="bg-white border-2 border-dashed border-gray-300 rounded-xl p-6 text-center h-full">
                  <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
                    <svg className="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-medium text-black mb-2">Create Another Portfolio</h3>
                  <p className="text-gray-600 mb-4">
                    You can create up to 3 portfolios ({3 - portfolios.length} remaining)
                  </p>
                  <button
                    onClick={handleCreatePortfolioClick}
                    className="px-6 py-2.5 bg-black text-white font-medium rounded-lg hover:bg-gray-800 transition-colors w-full sm:w-auto"
                  >
                    Create New Portfolio
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
      {/* Portfolio Allocation Chart Section - Only show when we have portfolios */}
      {!showPortfolioForm && portfolios.length > 0 && (
        <div className="mb-8">
          <PortfolioAllocationChart 
            portfolios={portfolios}
            individualPrices={individualPrices}
            performanceError={performanceError}
            performanceLoading={performanceLoading}
          />
        </div>
      )}
      {/* Portfolio Projection Section - Only show when we have portfolios */}
      {!showPortfolioForm && portfolios.length > 0 && (
        <PortfolioProjection 
          portfolios={portfolios}
          performanceError={performanceError}
        />
      )}
      {/* Price Changes Table - Only show if portfolios exist */}
      {!showPortfolioForm && portfolios.length > 0 && (
        <PriceChangesTable portfolios={portfolios} />
      )}
    </div>
  );
};

export default Dashboard;