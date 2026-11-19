import { useState } from 'react';
import { iniciarSesion } from '../services/api';

function Login({ onLogin }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [cargando, setCargando] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError('');
    setCargando(true);

    try {
      const { token, usuario } = await iniciarSesion(email, password);
      onLogin(token, usuario);
    } catch (err) {
      setError(err.message);
    } finally {
      setCargando(false);
    }
  }

  return (
    <section className="login-layout">
      <div className="login-presentacion" aria-hidden="true">
        <span className="login-presentacion-etiqueta">Gestión inteligente</span>
        <h2>Controla tu inventario con claridad</h2>
        <ul className="login-presentacion-lista">
          <li>Revisa el stock de tus productos en un solo lugar</li>
          <li>Registra salidas escaneando el código QR</li>
          <li>Recibe alertas cuando algo se esté acabando</li>
        </ul>
      </div>

      <form className="login-tarjeta" onSubmit={handleSubmit}>
        <div className="login-marca">
          <span className="login-marca-icono" aria-hidden="true">CS</span>
          <span>CogniStock</span>
        </div>
        <h1>Bienvenido</h1>
        <p className="subtitulo">Inicia sesión para continuar</p>

        <label htmlFor="email">Email o usuario</label>
        <input
          id="email"
          type="text"
          autoComplete="username"
          autoCapitalize="none"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />

        <label htmlFor="password">Contraseña</label>
        <input
          id="password"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />

        {error && <p className="error">{error}</p>}

        <button type="submit" disabled={cargando}>
          {cargando ? 'Ingresando...' : 'Ingresar'}
        </button>
      </form>
    </section>
  );
}

export default Login;