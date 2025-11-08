import React, { useEffect, useState } from 'react';
import { api } from '../api';
import { clearAuthToken } from '../token';

export const AuthStatus: React.FC = () => {
  const [displayName, setDisplayName] = useState<string | null>(null);
  const [connected, setConnected] = useState<boolean>(false);

  useEffect(() => {
    const run = async () => {
      try {
        const { data } = await api.get('/auth/status');
        if (data.logged_in && data.provider === 'spotify') {
          setDisplayName(data.display_name || null);
          setConnected(true);
        } else {
          setDisplayName(null);
          setConnected(false);
        }
      } catch {
        setDisplayName(null);
        setConnected(false);
      }
    };
    run();
  }, []);

  if (!connected) return null;

  return (
    <div className="auth-status">
      <div className="auth-status-pill">
        <span className="auth-status-spotify-dot" aria-hidden="true" />
        <span className="auth-status-label-text">Spotify linked</span>
        <span className="auth-status-name">{displayName || 'Anonymous listener'}</span>
      </div>
      <button
        className="auth-status-refresh"
        onClick={async () => {
          await api.post('/import/spotify/top-albums');
          window.location.reload();
        }}
      >
        Refresh albums
      </button>
    </div>
  );
};
