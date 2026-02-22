import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import '../styles/Favorites.css';

interface Favorite {
  id: number;
  listing_id: number;
  created_at: string;
}

interface FavoritesProps {
  token: string;
}

export function Favorites({ token }: FavoritesProps) {
  const [favorites, setFavorites] = useState<Favorite[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchFavorites();
  }, [token]);

  const fetchFavorites = async () => {
    try {
      setLoading(true);
      const response = await api.get('/user/favorites', {
        headers: { Authorization: `Bearer ${token}` },
      });
      setFavorites(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors du chargement des favoris');
    } finally {
      setLoading(false);
    }
  };

  const removeFavorite = async (listingId: number) => {
    try {
      await api.delete(`/user/favorites/${listingId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setFavorites(favorites.filter(f => f.listing_id !== listingId));
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors de la suppression');
    }
  };

  if (loading) return <div className="loading">Chargement...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="favorites-container">
      <h2>Mes Favoris ({favorites.length})</h2>
      
      {favorites.length === 0 ? (
        <div className="empty-state">
          <p>Vous n'avez pas encore de favoris</p>
        </div>
      ) : (
        <div className="favorites-list">
          {favorites.map(favorite => (
            <div key={favorite.id} className="favorite-item">
              <div className="favorite-info">
                <p>Annonce #{favorite.listing_id}</p>
                <small>{new Date(favorite.created_at).toLocaleDateString('fr-FR')}</small>
              </div>
              <button
                onClick={() => removeFavorite(favorite.listing_id)}
                className="remove-btn"
              >
                ✕ Supprimer
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
