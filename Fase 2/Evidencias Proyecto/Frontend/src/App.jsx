import { useEffect, useState } from 'react';

function App() {
  const [estado, setEstado] = useState('Comprobando conexión...');
  const [error, setError] = useState('');

  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/health/')
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Error HTTP: ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        setEstado(data.status);
      })
      .catch((error) => {
        setEstado('Error');
        setError(error.message);
      });
  }, []);

  return (
    <div>
      <h1>CogniStock</h1>

      <h2>Conexión con Backend</h2>

      <p>
        Estado del backend: <strong>{estado}</strong>
      </p>

      {error && <p>{error}</p>}
    </div>
  );
}

export default App;
