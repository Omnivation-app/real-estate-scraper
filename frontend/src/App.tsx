import { useState, useEffect } from 'react';
import { Auth } from './components/Auth';
import { Favorites } from './components/Favorites';
import { SearchAlerts } from './components/SearchAlerts';
import { MapViewer } from './components/MapViewer';
import './App.css';

function App() {
  const [token, setToken] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'search' | 'alerts' | 'favorites' | 'maps'>('search');

  useEffect(() => {
    // Récupérer le token du localStorage
    const savedToken = localStorage.getItem('token');
    if (savedToken) {
      setToken(savedToken);
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setActiveTab('search');
  };

  if (!token) {
    return <Auth onAuthSuccess={setToken} />;
  }

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="header-content">
          <h1>🏠 Real Estate Scraper</h1>
          <button onClick={handleLogout} className="logout-btn">
            Déconnexion
          </button>
        </div>
      </header>

      <nav className="app-nav">
        <button
          className={`nav-btn ${activeTab === 'search' ? 'active' : ''}`}
          onClick={() => setActiveTab('search')}
        >
          🔍 Recherche
        </button>
        <button
          className={`nav-btn ${activeTab === 'alerts' ? 'active' : ''}`}
          onClick={() => setActiveTab('alerts')}
        >
          🔔 Alertes
        </button>
        <button
          className={`nav-btn ${activeTab === 'favorites' ? 'active' : ''}`}
          onClick={() => setActiveTab('favorites')}
        >
          ⭐ Favoris
        </button>
        <button
          className={`nav-btn ${activeTab === 'maps' ? 'active' : ''}`}
          onClick={() => setActiveTab('maps')}
        >
          🗺️ Cartes
        </button>
      </nav>

      <main className="app-main">
        {activeTab === 'search' && (
          <div className="tab-content">
            <h2>Recherche d'Annonces</h2>
            <p>Fonctionnalité de recherche à implémenter...</p>
          </div>
        )}

        {activeTab === 'alerts' && (
          <SearchAlerts token={token} />
        )}

        {activeTab === 'favorites' && (
          <Favorites token={token} />
        )}

        {activeTab === 'maps' && (
          <MapViewer token={token} />
        )}
      </main>

      <footer className="app-footer">
        <p>&copy; 2026 Real Estate Scraper. Tous droits réservés.</p>
      </footer>
    </div>
  );
}

export default App;
