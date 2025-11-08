import React from 'react';
import { api } from '../api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const ConnectSpotify: React.FC = () => {
  const [connected, setConnected] = React.useState(false);

  React.useEffect(() => {
    api.get('/auth/status')
      .then((res) => {
        if (res.data.logged_in && res.data.provider === 'spotify') setConnected(true);
      })
      .catch(() => setConnected(false));
  }, []);

  if (connected) return null;

  const connect = () => {
    window.location.href = `${API_BASE_URL}/auth/spotify/login`;
  };

  return (
    <button onClick={connect} className="connect-spotify">
      <span className="spotify-logo" aria-hidden="true">
        <svg viewBox="0 0 168 168" className="spotify-logo-svg">
          <circle cx="84" cy="84" r="84" fill="#1DB954" />
          <path
            d="M120.1 115.3c-1.5 2.5-4.7 3.3-7.2 1.8c-19.8-12.1-44.7-14.8-74.1-8c-2.9.7-5.8-1.1-6.5-4.1c-.7-2.9 1.1-5.8 4.1-6.5c32.3-7.3 60.1-4.1 82.3 9.2c2.5 1.5 3.3 4.7 1.8 7.6zm9.9-23.4c-1.9 3-5.9 4-8.9 2.2c-22.7-14-57.3-18.1-84.1-9.8c-3.3 1-6.8-.8-7.8-4.1c-1-3.3.8-6.8 4.1-7.8c30.9-9.4 69.4-4.9 95.3 11.1c3 1.8 4 5.9 1.4 8.4zm1-24.5c-26-15.4-68.9-16.8-93.6-9.1c-4 1.3-8.3-1-9.6-5.1c-1.3-4 1-8.3 5.1-9.6c28.9-9 76.6-7.4 106.6 10.3c3.6 2.1 4.8 6.7 2.7 10.3c-2.1 3.6-6.7 4.8-10.3 2.7z"
            fill="#000"
          />
        </svg>
      </span>
      <span>Connect Spotify</span>
    </button>
  );
};
