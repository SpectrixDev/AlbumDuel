import React, { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { setAuthToken } from '../token';

export const SpotifyCallback: React.FC = () => {
  const [params] = useSearchParams();
  const navigate = useNavigate();

  useEffect(() => {
    const token = params.get('token');
    if (token) {
      setAuthToken(token);
      navigate('/', { replace: true });
    } else {
      navigate('/', { replace: true });
    }
  }, [params, navigate]);

  return <div>Connecting your Spotify account...</div>;
};
