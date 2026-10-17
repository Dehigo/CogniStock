import { useState } from 'react';
import { iniciarSesion } from './api';

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
    <form className="tarjeta" onSubmit={handleSubmit}>
      <h1>CogniStock</h1>
      <p className="subtitulo">Inicia sesión para continuar</p>

      <label htmlFor="email">Email</label>
      <input
        id="email"
        type="email"
        autoComplete="email"
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
  );
}

export default Login;
