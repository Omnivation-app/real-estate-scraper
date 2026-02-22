import React, { useState } from 'react';
import { api } from '../services/api';
import '../styles/Auth.css';

interface AuthProps {
  onAuthSuccess: (token: string) => void;
}

export function Auth({ onAuthSuccess }: AuthProps) {
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    fullName: '',
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (isLogin) {
        // Connexion
        const response = await api.post('/auth/login', {
          username: formData.username,
          password: formData.password,
        });
        localStorage.setItem('token', response.data.access_token);
        onAuthSuccess(response.data.access_token);
      } else {
        // Enregistrement
        const response = await api.post('/auth/register', {
          email: formData.email,
          username: formData.username,
          password: formData.password,
          full_name: formData.fullName,
        });
        // Connexion automatique après enregistrement
        const loginResponse = await api.post('/auth/login', {
          username: formData.username,
          password: formData.password,
        });
        localStorage.setItem('token', loginResponse.data.access_token);
        onAuthSuccess(loginResponse.data.access_token);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Une erreur s\'est produite');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h1>{isLogin ? 'Connexion' : 'Enregistrement'}</h1>
        
        {error && <div className="error-message">{error}</div>}
        
        <form onSubmit={handleSubmit}>
          {!isLogin && (
            <>
              <div className="form-group">
                <label>Email</label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  required
                  placeholder="votre@email.com"
                />
              </div>
              
              <div className="form-group">
                <label>Nom complet</label>
                <input
                  type="text"
                  name="fullName"
                  value={formData.fullName}
                  onChange={handleChange}
                  placeholder="Votre nom"
                />
              </div>
            </>
          )}
          
          <div className="form-group">
            <label>Nom d'utilisateur</label>
            <input
              type="text"
              name="username"
              value={formData.username}
              onChange={handleChange}
              required
              placeholder="username"
            />
          </div>
          
          <div className="form-group">
            <label>Mot de passe</label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              placeholder="••••••••"
            />
          </div>
          
          <button type="submit" disabled={loading} className="submit-btn">
            {loading ? 'Chargement...' : (isLogin ? 'Se connecter' : 'S\'enregistrer')}
          </button>
        </form>
        
        <div className="auth-toggle">
          {isLogin ? (
            <>
              Pas encore de compte?{' '}
              <button onClick={() => setIsLogin(false)} className="link-btn">
                S'enregistrer
              </button>
            </>
          ) : (
            <>
              Déjà un compte?{' '}
              <button onClick={() => setIsLogin(true)} className="link-btn">
                Se connecter
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
