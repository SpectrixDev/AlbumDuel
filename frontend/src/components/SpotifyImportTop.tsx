import React, { useState } from 'react';
import { api } from '../api';

export const SpotifyImportTop: React.FC = () => {
  const [status, setStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [maxAlbums, setMaxAlbums] = useState<number | null>(null);
  const [open, setOpen] = useState(false);

  const run = async () => {
    setLoading(true);
    setStatus(null);
    try {
      const { data } = await api.post('/import/spotify/top-albums', {
        max_albums: maxAlbums ?? undefined,
      });
      if (data.status === 'ok') {
        setStatus(
          `Imported ${data.imported} albums from your saved tracks (cap: ${data.max_albums}).`
        );
      } else {
        setStatus('Spotify import not configured.');
      }
    } catch (e: any) {
      setStatus(e.response?.data?.detail || 'Spotify import failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="spotify-import">
      <div className="spotify-import-header">
        <div>
          <div className="spotify-import-title">Spotify Album Sync</div>
          <div className="spotify-import-subtitle">
            Pulls full-length albums from your saved tracks; adjust the cap if needed.
          </div>
        </div>
        <button
          type="button"
          className="spotify-import-toggle"
          onClick={() => setOpen((v) => !v)}
        >
          {open ? 'Hide' : 'Show'} options
        </button>
      </div>
      {open && (
      <div className="spotify-import-controls">
        <label>
          Max albums (optional):
          <input
            type="number"
            min={10}
            max={2000}
            step={10}
            value={maxAlbums ?? ''}
            onChange={(e) => {
              const val = Number(e.target.value);
              setMaxAlbums(Number.isNaN(val) ? null : val);
            }}
          />
        </label>
      </div>
      )}
      <button onClick={run} disabled={loading}>
        {loading ? 'Refreshing…' : 'Refresh Spotify Albums'}
      </button>
      {status && <div className="status">{status}</div>}
    </div>
  );
};
