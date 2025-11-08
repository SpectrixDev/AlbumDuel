import React from 'react';
import { api } from '../api';

export const LastfmConnect: React.FC = () => {
  const handleConnect = async () => {
    const { data } = await api.get('/auth/lastfm/login', { maxRedirects: 0, validateStatus: () => true });
    if (typeof data === 'string') {
      window.location.href = data;
    } else if (data?.url) {
      window.location.href = data.url;
    }
  };

  const handleImport = async () => {
    await api.post('/import/lastfm/top-albums');
    window.location.reload();
  };

  return (
    <div className="lastfm-connect">
      <button className="lastfm-btn" onClick={handleConnect}>
        <span className="lastfm-dot" aria-hidden="true" />
        Connect Last.fm
      </button>
      <button className="lastfm-btn secondary" onClick={handleImport}>
        Import Last.fm top albums
      </button>
    </div>
  );
};
