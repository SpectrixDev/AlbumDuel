import React, { useEffect, useState } from 'react';
import { api } from '../api';

interface StatsResponse {
  total_albums: number;
  total_comparisons: number;
}

export const Stats: React.FC = () => {
  const [stats, setStats] = useState<StatsResponse | null>(null);

  useEffect(() => {
    api.get<StatsResponse>('/stats').then((res) => setStats(res.data));
  }, []);

  if (!stats) return <div>Loading...</div>;

  return (
    <div className="stats">
      <h2>Stats</h2>
      <p>Total albums ranked: {stats.total_albums}</p>
      <p>Total comparisons made: {stats.total_comparisons}</p>
    </div>
  );
};
