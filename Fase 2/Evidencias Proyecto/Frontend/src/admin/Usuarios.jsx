import { useCallback, useEffect, useState } from 'react';
import { desactivarUsuario, editarUsuario, listarRoles, listarUsuarios } from '../api';
import UsuarioForm from './UsuarioForm';

function formatearFecha(fecha) {
  if (!fecha) return 'Nunca';
  return new Date(fecha).toLocaleString('es-CL', { dateStyle: 'short', timeStyle: 'short' });
}

function Usuarios({ token, usuarioActual }) {
  const [usuarios, setUsuarios] = useState([]);
  const [roles, setRoles] = useState([]);
  const [buscar, setBuscar] = useState('');
  const [estado, setEstado] = useState('');
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState('');
  const [formulario, setFormulario] = useState(null);

  const cargarUsuarios = useCallback(async () => {
    setCargando(true);
    setError('');
    try {
      setUsuarios(await listarUsuarios(token, { buscar, activo: estado }));
    } catch (err) {
      setError(err.message);
    } finally {
      setCargando(false);
    }
  }, [token, buscar, estado]);

  useEffect(() => {
    const espera = setTimeout(cargarUsuarios, 300);
    return () => clearTimeout(espera);
  }, [cargarUsuarios]);

  useEffect(() => {
    listarRoles(token).then(setRoles).catch((err) => setError(err.message));
  }, [token]);

  async function cambiarEstado(usuario) {
    const accion = usuario.activo ? 'desactivar' : 'reactivar';
    if (!window.confirm(`¿Seguro que quieres ${accion} a ${usuario.nombre}?`)) return;

    try {
      if (usuario.activo) {
        await desactivarUsuario(token, usuario.id);
      } else {
        await editarUsuario(token, usuario.id, { activo: true });
      }
      cargarUsuarios();
    } catch (err) {
      setError(err.message);
    }
  }

  function alGuardar() {
    setFormulario(null);
    cargarUsuarios();
  }

  return (
    <section>
      <div className="seccion-cabecera">
        <h2>Usuarios</h2>
        <button className="boton" onClick={() => setFormulario({ usuario: null })}>
          Nuevo usuario
        </button>
      </div>

      <div className="filtros">
        <input
          type="search"
          placeholder="Buscar por nombre o email"
          value={buscar}
          onChange={(e) => setBuscar(e.target.value)}
        />
        <select value={estado} onChange={(e) => setEstado(e.target.value)}>
          <option value="">Todos</option>
          <option value="true">Activos</option>
          <option value="false">Inactivos</option>
        </select>
      </div>

      {error && <p className="error">{error}</p>}

      <div className="tabla-contenedor">
        <table className="tabla">
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Email</th>
              <th>Rol</th>
              <th>Estado</th>
              <th>Último acceso</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {cargando && (
              <tr>
                <td colSpan="6" className="tabla-mensaje">Cargando usuarios...</td>
              </tr>
            )}

            {!cargando && usuarios.length === 0 && (
              <tr>
                <td colSpan="6" className="tabla-mensaje">No se encontraron usuarios.</td>
              </tr>
            )}

            {!cargando &&
              usuarios.map((usuario) => (
                <tr key={usuario.id}>
                  <td>{usuario.nombre}</td>
                  <td className="celda-email">{usuario.email}</td>
                  <td>{usuario.rol_nombre}</td>
                  <td className="sin-salto">
                    <span className={`estado ${usuario.activo ? 'estado-activo' : 'estado-inactivo'}`}>
                      {usuario.activo ? 'Activo' : 'Inactivo'}
                    </span>
                  </td>
                  <td className="sin-salto">{formatearFecha(usuario.ultimo_acceso)}</td>
                  <td className="tabla-acciones">
                    <button className="boton-enlace" onClick={() => setFormulario({ usuario })}>
                      Editar
                    </button>
                    {usuario.id !== usuarioActual.id && (
                      <button className="boton-enlace" onClick={() => cambiarEstado(usuario)}>
                        {usuario.activo ? 'Desactivar' : 'Reactivar'}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      {formulario && (
        <UsuarioForm
          token={token}
          usuario={formulario.usuario}
          roles={roles}
          esUsuarioActual={formulario.usuario?.id === usuarioActual.id}
          onGuardar={alGuardar}
          onCancelar={() => setFormulario(null)}
        />
      )}
    </section>
  );
}

export default Usuarios;
