import { useEffect, useState } from 'react';
import PanelAdmin from './pages/admin/PanelAdmin';
import { ROL_ADMINISTRADOR } from './pages/admin/secciones';
import { cerrarSesion, obtenerUsuario } from './services/api';
import Login from './pages/Login';
import './styles/login.css';

// La app de escritorio (NW.js) abre esta misma web con ?escritorio y es solo para administradores (D-12).
const ES_ESCRITORIO = new URLSearchParams(window.location.search).has('escritorio');

// Si es true (valor por defecto), el administrador solo puede entrar desde la app de escritorio.
// Para permitirle usar también la web, poner VITE_ADMIN_SOLO_ESCRITORIO=false en el .env del frontend.
const ADMIN_SOLO_ESCRITORIO = import.meta.env.VITE_ADMIN_SOLO_ESCRITORIO !== 'false';

// Devuelve el motivo por el que este usuario no puede entrar aquí, o null si puede.
function motivoBloqueo(usuario) {
  const esAdministrador = usuario.rol === ROL_ADMINISTRADOR;
  if (ES_ESCRITORIO && !esAdministrador) {
    return { titulo: 'Solo administradores', texto: 'La app de escritorio es para administrar y supervisar. Usa la versión web.' };
  }
  if (!ES_ESCRITORIO && esAdministrador && ADMIN_SOLO_ESCRITORIO) {
    return { titulo: 'Usa la app de escritorio', texto: 'El administrador trabaja desde la app de escritorio de CogniStock.' };
  }
  return null;
}

function App() {
  const [token, setToken] = useState(() => localStorage.getItem('token'));
  const [usuario, setUsuario] = useState(null);
  const [sinConexion, setSinConexion] = useState(false);

  useEffect(() => {
    if (!token || usuario || sinConexion) return;

    obtenerUsuario(token)
      .then(setUsuario)
      .catch((err) => {
        // Solo se cierra la sesión si el token ya no sirve; un corte de red no debe sacar al usuario.
        if (err.status !== 401) {
          setSinConexion(true);
          return;
        }
        localStorage.removeItem('token');
        setToken(null);
      });
  }, [token, usuario, sinConexion]);

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

  const bloqueo = usuario && motivoBloqueo(usuario);
  if (bloqueo) {
    return (
      <main className="contenedor">
        <section className="tarjeta">
          <h1>{bloqueo.titulo}</h1>
          <p className="subtitulo">{bloqueo.texto}</p>
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

      {token && !usuario && !sinConexion && <p>Cargando...</p>}

      {token && !usuario && sinConexion && (
        <section className="tarjeta">
          <h1>Sin conexión</h1>
          <p className="subtitulo">No se pudo conectar con el servidor.</p>
          <button onClick={() => setSinConexion(false)}>Reintentar</button>
        </section>
      )}
    </main>
  );
}

export default App;
