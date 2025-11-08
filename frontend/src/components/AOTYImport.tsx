import React, { useState } from 'react';
import { api } from '../api';

export const AOTYImport: React.FC = () => {
  const [username, setUsername] = useState('');
  const [status, setStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    if (!username.trim()) {
      setStatus('Enter your Album of the Year username first.');
      return;
    }
    setLoading(true);
    setStatus(null);
    try {
      const { data } = await api.post('/import/aoty/user-albums', {
        aoty_username: username.trim(),
      });
      if (data.status === 'ok') {
        setStatus(`Imported ${data.imported} albums from Album of the Year.`);
      } else {
        setStatus('AOTY import not available.');
      }
    } catch (e: any) {
      setStatus(e.response?.data?.detail || 'AOTY import failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="aoty-import">
      <div className="aoty-import-header">
        <div className="aoty-import-title">Album of the Year Sync</div>
        <div className="aoty-import-subtitle">
          Pull in everything you’ve rated on albumoftheyear.org as part of your pool.
        </div>
      </div>
      <div className="aoty-import-controls">
        <div className="aoty-import-label">AOTY username</div>
        <input
          type="text"
          placeholder="AOTY username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        <button className="aoty-import-button" onClick={run} disabled={loading}>
          {loading ? 'Syncing…' : 'Import AOTY Ratings'}
        </button>
      </div>
      {status && <div className="status">{status}</div>}
    </div>
  );
};
