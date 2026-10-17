import { useEffect, useState } from 'react';
import { listarBitacora } from '../../../services/api';

const SECCIONES = [
  { valor: '', nombre: 'Todas' },
  { valor: 'usuarios', nombre: 'Usuarios' },
  { valor: 'productos', nombre: 'Productos' },
  { valor: 'categorias', nombre: 'Categorías' },
  { valor: 'proveedores', nombre: 'Proveedores' },
  { valor: 'parametros', nombre: 'Parámetros' },
];

function formatearFecha(fecha) {
  return new Date(fecha).toLocaleString('es-CL', { dateStyle: 'short', timeStyle: 'short' });
}

function formatearAccion(accion) {
  const texto = accion.replaceAll('_', ' ').toLowerCase();
  return texto.charAt(0).toUpperCase() + texto.slice(1);
}

function Bitacora({ token }) {
  const [registros, setRegistros] = useState([]);
  const [entidad, setEntidad] = useState('');
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    listarBitacora(token, { entidad })
      .then((datos) => {
        setRegistros(datos);
        setError('');
      })
      .catch((err) => setError(err.message))
      .finally(() => setCargando(false));
  }, [token, entidad]);

  return (
    <section>
      <div className="seccion-cabecera">
        <h2>Bitácora</h2>
      </div>

      <div className="filtros">
        <select value={entidad} onChange={(e) => setEntidad(e.target.value)}>
          {SECCIONES.map((s) => (
            <option key={s.valor} value={s.valor}>
              {s.nombre}
            </option>
          ))}
        </select>
      </div>

      {error && <p className="error">{error}</p>}

      <div className="tabla-contenedor">
        <table className="tabla">
          <thead>
            <tr>
              <th>Fecha</th>
              <th>Usuario</th>
              <th>Acción</th>
              <th>Sección</th>
              <th>IP</th>
            </tr>
          </thead>
          <tbody>
            {cargando && (
              <tr>
                <td colSpan="5" className="tabla-mensaje">Cargando bitácora...</td>
              </tr>
            )}

            {!cargando && registros.length === 0 && (
              <tr>
                <td colSpan="5" className="tabla-mensaje">No hay registros.</td>
              </tr>
            )}

            {!cargando &&
              registros.map((registro) => (
                <tr key={registro.id}>
                  <td className="sin-salto">{formatearFecha(registro.fecha)}</td>
                  <td>{registro.usuario_nombre ?? registro.detalle?.email ?? 'Desconocido'}</td>
                  <td>{formatearAccion(registro.accion)}</td>
                  <td>{registro.entidad}</td>
                  <td className="sin-salto">{registro.ip}</td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
      <p className="ayuda">Se muestran los últimos 200 registros.</p>
    </section>
  );
}

export default Bitacora;
