import React, { useState } from 'react';
import { api } from '../services/api';
import '../styles/MapViewer.css';

interface MapViewerProps {
  token?: string;
}

export function MapViewer({ token }: MapViewerProps) {
  const [postalCode, setPostalCode] = useState('75015');
  const [mapType, setMapType] = useState<'listings' | 'agencies'>('listings');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mapUrl, setMapUrl] = useState<string | null>(null);

  const handleGenerateMap = async () => {
    try {
      setLoading(true);
      setError(null);

      const endpoint = mapType === 'listings'
        ? `/maps/listings-map/${postalCode}`
        : `/maps/agencies-map/${postalCode}`;

      const response = await api.get(endpoint, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        responseType: 'text',
      });

      // Créer un blob et une URL pour afficher la carte
      const blob = new Blob([response.data], { type: 'text/html' });
      const url = URL.createObjectURL(blob);
      setMapUrl(url);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors de la génération de la carte');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="map-viewer-container">
      <div className="map-controls">
        <h2>Cartes Interactives</h2>
        
        <div className="control-group">
          <label>Code postal</label>
          <input
            type="text"
            value={postalCode}
            onChange={(e) => setPostalCode(e.target.value)}
            placeholder="75015"
            maxLength="5"
          />
        </div>

        <div className="control-group">
          <label>Type de carte</label>
          <select value={mapType} onChange={(e) => setMapType(e.target.value as 'listings' | 'agencies')}>
            <option value="listings">Annonces</option>
            <option value="agencies">Agences</option>
          </select>
        </div>

        <button onClick={handleGenerateMap} disabled={loading} className="generate-btn">
          {loading ? 'Génération...' : '🗺️ Générer la carte'}
        </button>

        {error && <div className="error-message">{error}</div>}
      </div>

      {mapUrl && (
        <div className="map-display">
          <iframe
            srcDoc={mapUrl}
            style={{ width: '100%', height: '600px', border: 'none', borderRadius: '8px' }}
            title="Real Estate Map"
          />
        </div>
      )}
    </div>
  );
}
