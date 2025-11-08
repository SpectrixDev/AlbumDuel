import React, { useEffect, useState } from 'react';
import { api } from '../api';

interface RankingEntry {
  album: {
    id: number;
    title: string;
    artist: string;
    year?: number;
    cover_url?: string;
    spotify_id?: string;
    source?: string;
  };
  elo: number;
  rating_100: number;
  comparisons_count: number;
}

interface RankingsResponse {
  items: RankingEntry[];
}

export const Leaderboard: React.FC = () => {
  const [items, setItems] = useState<RankingEntry[]>([]);

  useEffect(() => {
    api.get<RankingsResponse>('/rankings').then((res) => setItems(res.data.items));
  }, []);

  if (!items.length) return <div>No rankings yet. Start dueling to see results.</div>;

  return (
    <div className="leaderboard">
      <h2>Your Rankings</h2>
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Album</th>
            <th>Artist</th>
            <th>Elo</th>
            <th>Rating /100</th>
            <th>Source</th>
            <th>Comparisons</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item, idx) => (
            <tr key={item.album.id}>
              <td>{idx + 1}</td>
              <td>{item.album.title}</td>
              <td>{item.album.artist}</td>
              <td>{item.elo.toFixed(0)}</td>
              <td>{item.rating_100.toFixed(1)}</td>
              <td className="source-cell">{item.album.source || (item.album.spotify_id ? 'Spotify' : 'AOTY')}</td>
              <td>{item.comparisons_count}</td>
              <td>
                <button
                  type="button"
                  className="exclude-button"
                  onClick={() =>
                    api.post('/albums/exclude', { album_id: item.album.id }).then(() =>
                      setItems((prev) => prev.filter((x) => x.album.id !== item.album.id)),
                    )
                  }
                >
                  Exclude
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
