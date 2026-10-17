import { useState } from 'react';
import { crearUsuario, editarUsuario } from '../api';

function UsuarioForm({ token, usuario, roles, esUsuarioActual, onGuardar, onCancelar }) {
  const esNuevo = usuario === null;
  const [nombre, setNombre] = useState(usuario?.nombre ?? '');
  const [email, setEmail] = useState(usuario?.email ?? '');
  const [rol, setRol] = useState(usuario?.rol ?? '');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [guardando, setGuardando] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError('');
    setGuardando(true);

    const datos = { nombre, email, rol: Number(rol) };
    if (password) datos.password = password;

    try {
      if (esNuevo) {
        await crearUsuario(token, datos);
      } else {
        await editarUsuario(token, usuario.id, datos);
      }
      onGuardar();
    } catch (err) {
      setError(err.message);
    } finally {
      setGuardando(false);
    }
  }

  return (
    <div className="modal-fondo" onClick={onCancelar}>
      <form className="modal" onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
        <h3>{esNuevo ? 'Nuevo usuario' : `Editar a ${usuario.nombre}`}</h3>

        <label htmlFor="nombre">Nombre</label>
        <input id="nombre" value={nombre} onChange={(e) => setNombre(e.target.value)} required />

        <label htmlFor="email">Email</label>
        <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />

        <label htmlFor="rol">Rol</label>
        <select
          id="rol"
          value={rol}
          onChange={(e) => setRol(e.target.value)}
          disabled={esUsuarioActual}
          required
        >
          <option value="" disabled>
            Selecciona un rol
          </option>
          {roles.map((r) => (
            <option key={r.id} value={r.id}>
              {r.nombre}
            </option>
          ))}
        </select>

        <label htmlFor="password">Contraseña</label>
        <input
          id="password"
          type="password"
          autoComplete="new-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder={esNuevo ? '' : 'Déjala vacía para no cambiarla'}
          required={esNuevo}
        />

        {error && <p className="error">{error}</p>}

        <div className="modal-acciones">
          <button type="button" className="boton boton-secundario" onClick={onCancelar}>
            Cancelar
          </button>
          <button type="submit" className="boton" disabled={guardando}>
            {guardando ? 'Guardando...' : 'Guardar'}
          </button>
        </div>
      </form>
    </div>
  );
}

export default UsuarioForm;
