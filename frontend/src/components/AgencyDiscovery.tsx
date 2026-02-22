import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import '../styles/AgencyDiscovery.css';

interface Agency {
  id: number;
  name: string;
  website_url: string;
  phone?: string;
  address?: string;
  postal_code?: string;
  city?: string;
  scraping_status: string;
  total_listings: number;
  active_listings: number;
  last_scraped?: string;
  discovered_from: string[];
}

interface DiscoveryResult {
  status: string;
  postal_code: string;
  agencies_discovered: number;
  agencies_saved: number;
  message: string;
}

export const AgencyDiscovery: React.FC = () => {
  const [postalCode, setPostalCode] = useState('75015');
  const [loading, setLoading] = useState(false);
  const [discovering, setDiscovering] = useState(false);
  const [agencies, setAgencies] = useState<Agency[]>([]);
  const [result, setResult] = useState<DiscoveryResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('name');

  // Charger les agences
  const loadAgencies = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get('/discovery/agencies', {
        params: {
          postal_code: postalCode,
          limit: 100
        }
      });
      
      let filtered = response.data.agencies;
      
      // Appliquer les filtres
      if (filter === 'pending') {
        filtered = filtered.filter((a: Agency) => a.scraping_status === 'pending');
      } else if (filter === 'active') {
        filtered = filtered.filter((a: Agency) => a.scraping_status === 'active');
      } else if (filter === 'success') {
        filtered = filtered.filter((a: Agency) => a.scraping_status === 'success');
      } else if (filter === 'failed') {
        filtered = filtered.filter((a: Agency) => a.scraping_status === 'failed');
      }
      
      // Appliquer le tri
      if (sortBy === 'name') {
        filtered.sort((a: Agency, b: Agency) => a.name.localeCompare(b.name));
      } else if (sortBy === 'listings') {
        filtered.sort((a: Agency, b: Agency) => b.total_listings - a.total_listings);
      } else if (sortBy === 'recent') {
        filtered.sort((a: Agency, b: Agency) => {
          const dateA = new Date(a.last_scraped || 0).getTime();
          const dateB = new Date(b.last_scraped || 0).getTime();
          return dateB - dateA;
        });
      }
      
      setAgencies(filtered);
    } catch (err) {
      setError('Erreur lors du chargement des agences');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Découvrir les agences
  const handleDiscover = async () => {
    setDiscovering(true);
    setError(null);
    try {
      const response = await api.post(`/discovery/discover-agencies/${postalCode}`);
      setResult(response.data);
      
      // Recharger les agences après la découverte
      setTimeout(() => {
        loadAgencies();
      }, 2000);
    } catch (err) {
      setError('Erreur lors de la découverte des agences');
      console.error(err);
    } finally {
      setDiscovering(false);
    }
  };

  // Scraper une agence
  const handleScrapeAgency = async (agencyId: number) => {
    try {
      await api.post(`/discovery/scrape-agency/${agencyId}`);
      setResult({
        status: 'scraping_started',
        postal_code: postalCode,
        agencies_discovered: 0,
        agencies_saved: 0,
        message: 'Scraping lancé en arrière-plan'
      });
      
      // Recharger après quelques secondes
      setTimeout(() => {
        loadAgencies();
      }, 3000);
    } catch (err) {
      setError('Erreur lors du scraping');
      console.error(err);
    }
  };

  // Scraper toutes les agences
  const handleScrapeAll = async () => {
    if (!window.confirm('Êtes-vous sûr de vouloir scraper toutes les agences ?')) {
      return;
    }
    
    try {
      await api.post('/discovery/scrape-all');
      setResult({
        status: 'scraping_started',
        postal_code: postalCode,
        agencies_discovered: 0,
        agencies_saved: 0,
        message: 'Scraping de toutes les agences lancé en arrière-plan'
      });
    } catch (err) {
      setError('Erreur lors du scraping');
      console.error(err);
    }
  };

  useEffect(() => {
    loadAgencies();
  }, [postalCode, filter, sortBy]);

  const getStatusBadge = (status: string) => {
    const statusMap: Record<string, { color: string; label: string }> = {
      pending: { color: '#ffc107', label: 'En attente' },
      active: { color: '#17a2b8', label: 'En cours' },
      success: { color: '#28a745', label: 'Succès' },
      failed: { color: '#dc3545', label: 'Échoué' },
      blocked: { color: '#6c757d', label: 'Bloqué' }
    };
    
    const info = statusMap[status] || { color: '#6c757d', label: status };
    return (
      <span style={{
        backgroundColor: info.color,
        color: 'white',
        padding: '4px 8px',
        borderRadius: '4px',
        fontSize: '12px',
        fontWeight: 'bold'
      }}>
        {info.label}
      </span>
    );
  };

  return (
    <div className="agency-discovery-container">
      <h1>🏢 Découverte et Scraping des Agences</h1>
      
      {error && (
        <div className="error-message">
          ⚠️ {error}
        </div>
      )}
      
      {result && (
        <div className="success-message">
          ✅ {result.message}
        </div>
      )}
      
      {/* Contrôles */}
      <div className="controls-section">
        <div className="control-group">
          <label>Code Postal :</label>
          <input
            type="text"
            value={postalCode}
            onChange={(e) => setPostalCode(e.target.value)}
            placeholder="75015"
            maxLength={5}
          />
        </div>
        
        <button
          onClick={handleDiscover}
          disabled={discovering || loading}
          className="btn-primary"
        >
          {discovering ? '🔍 Découverte en cours...' : '🔍 Découvrir les Agences'}
        </button>
        
        <button
          onClick={handleScrapeAll}
          disabled={loading || agencies.length === 0}
          className="btn-secondary"
        >
          📊 Scraper Toutes les Agences
        </button>
      </div>
      
      {/* Filtres et Tri */}
      <div className="filters-section">
        <div className="filter-group">
          <label>Filtrer par statut :</label>
          <select value={filter} onChange={(e) => setFilter(e.target.value)}>
            <option value="all">Tous</option>
            <option value="pending">En attente</option>
            <option value="active">En cours</option>
            <option value="success">Succès</option>
            <option value="failed">Échoué</option>
          </select>
        </div>
        
        <div className="filter-group">
          <label>Trier par :</label>
          <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
            <option value="name">Nom</option>
            <option value="listings">Nombre d'annonces</option>
            <option value="recent">Récemment scrapé</option>
          </select>
        </div>
      </div>
      
      {/* Statistiques */}
      <div className="stats-section">
        <div className="stat-card">
          <div className="stat-value">{agencies.length}</div>
          <div className="stat-label">Agences</div>
        </div>
        
        <div className="stat-card">
          <div className="stat-value">
            {agencies.reduce((sum, a) => sum + a.total_listings, 0)}
          </div>
          <div className="stat-label">Annonces Totales</div>
        </div>
        
        <div className="stat-card">
          <div className="stat-value">
            {agencies.filter(a => a.scraping_status === 'success').length}
          </div>
          <div className="stat-label">Scrapées</div>
        </div>
        
        <div className="stat-card">
          <div className="stat-value">
            {agencies.filter(a => a.scraping_status === 'pending').length}
          </div>
          <div className="stat-label">En Attente</div>
        </div>
      </div>
      
      {/* Liste des agences */}
      <div className="agencies-section">
        <h2>Agences ({agencies.length})</h2>
        
        {loading ? (
          <div className="loading">Chargement...</div>
        ) : agencies.length === 0 ? (
          <div className="no-data">Aucune agence trouvée</div>
        ) : (
          <div className="agencies-grid">
            {agencies.map((agency) => (
              <div key={agency.id} className="agency-card">
                <div className="agency-header">
                  <h3>{agency.name}</h3>
                  {getStatusBadge(agency.scraping_status)}
                </div>
                
                <div className="agency-info">
                  <p><strong>Site :</strong> <a href={agency.website_url} target="_blank" rel="noopener noreferrer">{agency.website_url}</a></p>
                  {agency.phone && <p><strong>Téléphone :</strong> {agency.phone}</p>}
                  {agency.address && <p><strong>Adresse :</strong> {agency.address}</p>}
                  {agency.city && <p><strong>Ville :</strong> {agency.city}</p>}
                </div>
                
                <div className="agency-stats">
                  <div className="stat">
                    <span className="stat-label">Annonces</span>
                    <span className="stat-value">{agency.total_listings}</span>
                  </div>
                  <div className="stat">
                    <span className="stat-label">Actives</span>
                    <span className="stat-value">{agency.active_listings}</span>
                  </div>
                  {agency.last_scraped && (
                    <div className="stat">
                      <span className="stat-label">Dernière MAJ</span>
                      <span className="stat-value">
                        {new Date(agency.last_scraped).toLocaleDateString('fr-FR')}
                      </span>
                    </div>
                  )}
                </div>
                
                <div className="agency-sources">
                  <strong>Découverte via :</strong>
                  <div className="sources-list">
                    {agency.discovered_from.map((source) => (
                      <span key={source} className="source-badge">{source}</span>
                    ))}
                  </div>
                </div>
                
                <button
                  onClick={() => handleScrapeAgency(agency.id)}
                  disabled={agency.scraping_status === 'active'}
                  className="btn-scrape"
                >
                  {agency.scraping_status === 'active' ? '⏳ Scraping...' : '📊 Scraper'}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
