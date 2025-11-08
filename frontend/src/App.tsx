import React from 'react';
import { Routes, Route, Link } from 'react-router-dom';
import { Duel } from './components/Duel';
import { Leaderboard } from './components/Leaderboard';
import { Stats } from './components/Stats';
import { ConnectSpotify } from './components/ConnectSpotify';
import { SpotifyCallback } from './components/SpotifyCallback';
import { SpotifyImportTop } from './components/SpotifyImportTop';
import { AOTYImport } from './components/AOTYImport';
import { AuthStatus } from './components/AuthStatus';
import { LastfmConnect } from './components/LastfmConnect';
import { Sources } from './components/Sources';
import { Swords, BarChart2, Activity } from 'lucide-react';

export const App: React.FC = () => (
  <div className="app">
    <header className="header">
      <h1>
        <img src="/AlbumDuel/favicon.svg" alt="AlbumDuel" style={{ width: '24px', height: '24px', marginRight: '8px', verticalAlign: 'middle' }} />
        AlbumDuel
      </h1>
      <nav>
        <Link to="/">
          <Swords size={16} />
          <span>Duel</span>
        </Link>
        <Link to="/leaderboard">
          <BarChart2 size={16} />
          <span>Leaderboard</span>
        </Link>
        <Link to="/stats">
          <Activity size={16} />
          <span>Stats</span>
        </Link>
        <Link to="/sources">
          <span>Sources</span>
        </Link>
      </nav>
    </header>
    <main>
      <Routes>
        <Route path="/" element={<Duel />} />
        <Route path="/leaderboard" element={<Leaderboard />} />
        <Route path="/stats" element={<Stats />} />
        <Route path="/sources" element={<Sources />} />
        <Route path="/auth/spotify/callback" element={<SpotifyCallback />} />
      </Routes>
    </main>
  </div>
);
