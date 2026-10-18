import { useEffect, useState } from 'react';
import PanelAdmin from './pages/admin/PanelAdmin';
import { cerrarSesion, obtenerUsuario } from './services/api';
import Login from './pages/Login';
import './styles/login.css';

function App() {
  const [token, setToken] = useState(() => localStorage.getItem('token'));
  const [usuario, setUsuario] = useState(null);

  useEffect(() => {
    if (!token || usuario) return;

    obtenerUsuario(token)
      .then(setUsuario)
      .catch(() => {
        localStorage.removeItem('token');
        setToken(null);
      });
  }, [token, usuario]);

  function handleLogin(nuevoToken, datosUsuario) {
    localStorage.setItem('token', nuevoToken);
    setToken(nuevoToken);
    setUsuario(datosUsuario);
  }

  async function handleLogout() {
    try {
      await cerrarSesion(token);
    } finally {
      localStorage.removeItem('token');
      setToken(null);
      setUsuario(null);
    }
  }

  if (usuario) {
    return <PanelAdmin token={token} usuario={usuario} onLogout={handleLogout} />;
  }

  return (
    <main className="contenedor">
      {!token && <Login onLogin={handleLogin} />}

      {token && !usuario && <p>Cargando...</p>}
    </main>
  );
}

export default App;
