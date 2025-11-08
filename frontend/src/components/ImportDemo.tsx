import React, { useState } from 'react';
import { api } from '../api';

export const ImportDemo: React.FC = () => {
  const [status, setStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const runImport = async () => {
    setLoading(true);
    setStatus(null);
    try {
      const { data } = await api.post('/import/demo-albums');
      setStatus(`Imported ${data.created_albums} albums (or already present).`);
    } catch (e: any) {
      setStatus('Import failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="import-demo">
      <button onClick={runImport} disabled={loading}>
        {loading ? 'Importing…' : 'Import demo albums'}
      </button>
      {status && <div className="status">{status}</div>}
    </div>
  );
};
