import React, { useEffect, useState } from 'react';
import { api } from '../api';

interface StatsResponse {
  total_albums: number;
  total_comparisons: number;
}

const formatNumber = (n: number) => n.toLocaleString();

export const Stats: React.FC = () => {
  const [stats, setStats] = useState<StatsResponse | null>(null);

  useEffect(() => {
    api.get<StatsResponse>('/stats').then((res) => setStats(res.data));
  }, []);

  if (!stats) return <div className="stats">Loading your duel stats...</div>;

  const avgComparisonsPerAlbum = stats.total_albums
    ? stats.total_comparisons / stats.total_albums
    : 0;

  return (
    <div className="stats">
      <h2>Your Duel Stats</h2>
      <div className="stats-grid">
        <div className="stat-card primary">
          <div className="stat-label">Albums Ranked</div>
          <div className="stat-value">{formatNumber(stats.total_albums)}</div>
          <div className="stat-sub">Unique albums currently in your Elo ladder.</div>
          <div className="stat-bar-wrapper">
            <div
              className="stat-bar"
              style={{ width: `${Math.min(100, (stats.total_albums / 250) * 100)}%` }}
            />
          </div>
        </div>
        <div className="stat-card primary">
          <div className="stat-label">Total Duels</div>
          <div className="stat-value">{formatNumber(stats.total_comparisons)}</div>
          <div className="stat-sub">Every time you picked a winner between two albums.</div>
          <div className="stat-bar-wrapper">
            <div
              className="stat-bar"
              style={{ width: `${Math.min(100, (stats.total_comparisons / 1000) * 100)}%` }}
            />
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Duels per Album</div>
          <div className="stat-value">{avgComparisonsPerAlbum.toFixed(2)}</div>
          <div className="stat-sub">How deeply you&apos;ve ranked each album on average.</div>
          <div className="stat-bar-wrapper">
            <div
              className="stat-bar"
              style={{ width: `${Math.min(100, (avgComparisonsPerAlbum / 10) * 100)}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
