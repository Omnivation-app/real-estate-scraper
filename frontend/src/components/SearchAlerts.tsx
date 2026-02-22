import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import '../styles/SearchAlerts.css';

interface SearchAlert {
  id: number;
  name: string;
  postal_code: string;
  min_price: number | null;
  max_price: number | null;
  min_surface: number | null;
  property_type: string | null;
  is_active: boolean;
  created_at: string;
}

interface SearchAlertsProps {
  token: string;
}

export function SearchAlerts({ token }: SearchAlertsProps) {
  const [alerts, setAlerts] = useState<SearchAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    postal_code: '',
    min_price: '',
    max_price: '',
    min_surface: '',
    property_type: '',
  });

  useEffect(() => {
    fetchAlerts();
  }, [token]);

  const fetchAlerts = async () => {
    try {
      setLoading(true);
      const response = await api.get('/user/alerts', {
        headers: { Authorization: `Bearer ${token}` },
      });
      setAlerts(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors du chargement des alertes');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload = {
        name: formData.name,
        postal_code: formData.postal_code,
        min_price: formData.min_price ? parseFloat(formData.min_price) : null,
        max_price: formData.max_price ? parseFloat(formData.max_price) : null,
        min_surface: formData.min_surface ? parseFloat(formData.min_surface) : null,
        property_type: formData.property_type || null,
      };

      await api.post('/user/alerts', payload, {
        headers: { Authorization: `Bearer ${token}` },
      });

      setFormData({
        name: '',
        postal_code: '',
        min_price: '',
        max_price: '',
        min_surface: '',
        property_type: '',
      });
      setShowForm(false);
      fetchAlerts();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors de la création de l\'alerte');
    }
  };

  const deleteAlert = async (alertId: number) => {
    try {
      await api.delete(`/user/alerts/${alertId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      fetchAlerts();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors de la suppression');
    }
  };

  const toggleAlert = async (alertId: number) => {
    try {
      await api.post(`/user/alerts/${alertId}/toggle`, {}, {
        headers: { Authorization: `Bearer ${token}` },
      });
      fetchAlerts();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors de la modification');
    }
  };

  if (loading) return <div className="loading">Chargement...</div>;

  return (
    <div className="alerts-container">
      <div className="alerts-header">
        <h2>Mes Alertes de Recherche ({alerts.length})</h2>
        <button onClick={() => setShowForm(!showForm)} className="add-btn">
          + Nouvelle alerte
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      {showForm && (
        <form onSubmit={handleSubmit} className="alert-form">
          <div className="form-group">
            <label>Nom de l'alerte</label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              required
              placeholder="ex: Appartements Paris 75015"
            />
          </div>

          <div className="form-group">
            <label>Code postal</label>
            <input
              type="text"
              name="postal_code"
              value={formData.postal_code}
              onChange={handleChange}
              required
              placeholder="75015"
              maxLength="5"
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Prix min (€)</label>
              <input
                type="number"
                name="min_price"
                value={formData.min_price}
                onChange={handleChange}
                placeholder="200000"
              />
            </div>

            <div className="form-group">
              <label>Prix max (€)</label>
              <input
                type="number"
                name="max_price"
                value={formData.max_price}
                onChange={handleChange}
                placeholder="500000"
              />
            </div>
          </div>

          <div className="form-group">
            <label>Surface min (m²)</label>
            <input
              type="number"
              name="min_surface"
              value={formData.min_surface}
              onChange={handleChange}
              placeholder="50"
            />
          </div>

          <div className="form-group">
            <label>Type de bien</label>
            <select name="property_type" value={formData.property_type} onChange={handleChange}>
              <option value="">Tous les types</option>
              <option value="apartment">Appartement</option>
              <option value="house">Maison</option>
              <option value="land">Terrain</option>
              <option value="commercial">Commercial</option>
            </select>
          </div>

          <div className="form-actions">
            <button type="submit" className="submit-btn">Créer l'alerte</button>
            <button type="button" onClick={() => setShowForm(false)} className="cancel-btn">
              Annuler
            </button>
          </div>
        </form>
      )}

      {alerts.length === 0 ? (
        <div className="empty-state">
          <p>Vous n'avez pas encore d'alertes</p>
        </div>
      ) : (
        <div className="alerts-list">
          {alerts.map(alert => (
            <div key={alert.id} className={`alert-item ${alert.is_active ? 'active' : 'inactive'}`}>
              <div className="alert-content">
                <h3>{alert.name}</h3>
                <div className="alert-details">
                  <span>📍 {alert.postal_code}</span>
                  {alert.min_price && <span>💰 {alert.min_price.toLocaleString()}€ - {alert.max_price?.toLocaleString()}€</span>}
                  {alert.min_surface && <span>📐 {alert.min_surface}m²+</span>}
                  {alert.property_type && <span>🏠 {alert.property_type}</span>}
                </div>
                <small>Créée le {new Date(alert.created_at).toLocaleDateString('fr-FR')}</small>
              </div>
              <div className="alert-actions">
                <button
                  onClick={() => toggleAlert(alert.id)}
                  className={`toggle-btn ${alert.is_active ? 'active' : ''}`}
                >
                  {alert.is_active ? '✓ Actif' : '✗ Inactif'}
                </button>
                <button
                  onClick={() => deleteAlert(alert.id)}
                  className="delete-btn"
                >
                  🗑️ Supprimer
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
