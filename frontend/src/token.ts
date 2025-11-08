let authToken: string | null = null;

export const setAuthToken = (token: string) => {
  authToken = token;
  try {
    localStorage.setItem('albumduel_token', token);
  } catch {
    // ignore
  }
};

export const getAuthToken = (): string | null => {
  if (authToken) return authToken;
  try {
    const stored = localStorage.getItem('albumduel_token');
    if (stored) authToken = stored;
  } catch {
    // ignore
  }
  return authToken;
};

export const clearAuthToken = () => {
  authToken = null;
  try {
    localStorage.removeItem('albumduel_token');
  } catch {
    // ignore
  }
};
