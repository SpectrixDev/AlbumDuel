import type { Album } from './components/Duel';

const PLACEHOLDER_BASE = 'https://placehold.co/300x300/15131f/c4a7e7?text=';

export function getAlbumCoverUrl(album: Pick<Album, 'title' | 'artist' | 'cover_url'>): string {
  if (album.cover_url && album.cover_url.trim()) return album.cover_url;
  const label = encodeURIComponent(`${album.artist} • ${album.title}`);
  return `${PLACEHOLDER_BASE}${label}`;
}
