import { useEffect, useState } from 'react';
import PanelAdmin from './pages/admin/PanelAdmin';
import { ROL_ADMINISTRADOR } from './pages/admin/secciones';
import { cerrarSesion, obtenerUsuario } from './services/api';
import Login from './pages/Login';
import './styles/login.css';

// La app de escritorio (NW.js) abre esta misma web con ?escritorio y es solo para administradores (D-12).
const ES_ESCRITORIO = new URLSearchParams(window.location.search).has('escritorio');

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

  if (usuario && ES_ESCRITORIO && usuario.rol !== ROL_ADMINISTRADOR) {
    return (
      <main className="contenedor">
        <section className="tarjeta">
          <h1>Solo administradores</h1>
          <p className="subtitulo">La app de escritorio es para administrar y supervisar. Usa la versión web.</p>
          <button onClick={handleLogout}>Cerrar sesión</button>
        </section>
      </main>
    );
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
