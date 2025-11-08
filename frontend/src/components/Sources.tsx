import React from 'react';
import { ConnectSpotify } from './ConnectSpotify';
import { AuthStatus } from './AuthStatus';
import { SpotifyImportTop } from './SpotifyImportTop';
import { AOTYImport } from './AOTYImport';
import { LastfmConnect } from './LastfmConnect';

export const Sources: React.FC = () => {
  return (
    <div className="sources-page">
      <h2>Sources</h2>
      <p>Connect and manage all sources used to build your AlbumDuel pool.</p>
      <section>
        <h3>Spotify</h3>
        <ConnectSpotify />
        <AuthStatus />
        <SpotifyImportTop />
      </section>
      <section>
        <h3>Last.fm</h3>
        <LastfmConnect />
      </section>
      <section>
        <h3>Album of the Year (AOTY)</h3>
        <AOTYImport />
      </section>
    </div>
  );
};
