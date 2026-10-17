import { useEffect, useState } from 'react';
import PanelAdmin from './pages/admin/PanelAdmin';
import { cerrarSesion, obtenerUsuario } from './services/api';
import Login from './pages/Login';
import './styles/login.css';

const ROL_ADMINISTRADOR = 'Administrador';

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

  if (usuario?.rol === ROL_ADMINISTRADOR) {
    return <PanelAdmin token={token} usuario={usuario} onLogout={handleLogout} />;
  }

  return (
    <main className="contenedor">
      {!token && <Login onLogin={handleLogin} />}

      {token && !usuario && <p>Cargando...</p>}

      {usuario && (
        <section className="tarjeta">
          <h1>Hola, {usuario.nombre}</h1>
          <p className="subtitulo">Sesión iniciada correctamente</p>
          <dl>
            <dt>Email</dt>
            <dd>{usuario.email}</dd>
            <dt>Rol</dt>
            <dd>{usuario.rol}</dd>
          </dl>
          <button onClick={handleLogout}>Cerrar sesión</button>
        </section>
      )}
    </main>
  );
}

export default App;
