import React, { useEffect, useState, useCallback } from 'react';
import { api } from '../api';

interface Album {
  id: number;
  title: string;
  artist: string;
  year?: number;
  cover_url?: string;
  spotify_id?: string;
  elo: number;
  comparisons_count: number;
}

interface PairResponse {
  album_a: Album;
  album_b: Album;
  total_comparisons: number;
}

export const Duel: React.FC = () => {
  const [pair, setPair] = useState<PairResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const loadPair = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await api.get<PairResponse>('/compare/next');
      setPair(data);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadPair();
  }, [loadPair]);

  const submit = async (winnerAlbumId: number | null) => {
    if (!pair) return;
    await api.post('/compare/submit', {
      album_a_id: pair.album_a.id,
      album_b_id: pair.album_b.id,
      winner_album_id: winnerAlbumId,
    });
    loadPair();
  };

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (!pair) return;
      if (e.key === 'ArrowLeft') submit(pair.album_a.id);
      if (e.key === 'ArrowRight') submit(pair.album_b.id);
      if (e.key === ' ') {
        e.preventDefault();
        submit(null);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [pair]);

  if (loading && !pair) return <div>Loading...</div>;
  if (!pair) return <div>No albums available. Import or add some to begin.</div>;

  return (
    <div className="duel">
      <div className="album" onClick={() => submit(pair.album_a.id)}>
        <div className="album-actions">
          {pair.album_a.spotify_id && (
            <a
              href={`https://open.spotify.com/album/${pair.album_a.spotify_id}`}
              target="_blank"
              rel="noopener noreferrer"
              className="spotify-link"
              onClick={(e) => e.stopPropagation()}
            >
              ♫
            </a>
          )}
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              api.post('/albums/exclude', { album_id: pair.album_a.id }).then(() => submit(null));
            }}
          >
            Exclude
          </button>
        </div>
        <img
          src={pair.album_a.cover_url || 'https://placehold.co/300x300/15131f/c4a7e7?text=AOTY+%E2%80%A2+No+Cover'}
          alt={pair.album_a.title}
          loading="lazy"
        />
        <h2>{pair.album_a.title}</h2>
        <p>{pair.album_a.artist}</p>
        {pair.album_a.year && <p>{pair.album_a.year}</p>}
      </div>
      <div className="vs">vs</div>
      <div className="album" onClick={() => submit(pair.album_b.id)}>
        <div className="album-actions">
          {pair.album_b.spotify_id && (
            <a
              href={`https://open.spotify.com/album/${pair.album_b.spotify_id}`}
              target="_blank"
              rel="noopener noreferrer"
              className="spotify-link"
              onClick={(e) => e.stopPropagation()}
            >
              ♫
            </a>
          )}
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              api.post('/albums/exclude', { album_id: pair.album_b.id }).then(() => submit(null));
            }}
          >
            Exclude
          </button>
        </div>
        <img
          src={pair.album_b.cover_url || 'https://placehold.co/300x300/15131f/c4a7e7?text=AOTY+%E2%80%A2+No+Cover'}
          alt={pair.album_b.title}
          loading="lazy"
        />
        <h2>{pair.album_b.title}</h2>
        <p>{pair.album_b.artist}</p>
        {pair.album_b.year && <p>{pair.album_b.year}</p>}
      </div>
      <div className="controls">
        <button onClick={() => submit(null)}>Skip (Space)</button>
        <div>Total comparisons: {pair.total_comparisons}</div>
      </div>
    </div>
  );
};
