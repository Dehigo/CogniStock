import { useCallback, useEffect, useState } from 'react';
import { listarMovimientos } from '../../../services/api';

function formatearFechaHora(fecha) {
  return new Date(fecha).toLocaleString('es-CL', { dateStyle: 'short', timeStyle: 'short' });
}

function Movimientos({ token }) {
  const [movimientos, setMovimientos] = useState([]);
  const [buscar, setBuscar] = useState('');
  const [tipo, setTipo] = useState('');
  const [desde, setDesde] = useState('');
  const [hasta, setHasta] = useState('');
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState('');

  const unidades = (t) => movimientos.filter((m) => m.tipo === t).reduce((suma, m) => suma + m.cantidad, 0);

  const cargarMovimientos = useCallback(async () => {
    try {
      setMovimientos(await listarMovimientos(token, { buscar, tipo, desde, hasta }));
      setError('');
    } catch (err) {
      setError(err.message);
    } finally {
      setCargando(false);
    }
  }, [token, buscar, tipo, desde, hasta]);

  useEffect(() => {
    const espera = setTimeout(cargarMovimientos, 300);
    return () => clearTimeout(espera);
  }, [cargarMovimientos]);

  function limpiarFiltros() {
    setBuscar('');
    setTipo('');
    setDesde('');
    setHasta('');
  }

  return (
    <section>
      <div className="seccion-cabecera">
        <h2>Movimientos</h2>
      </div>

      <div className="resumen-grid">
        <div className="tarjeta-resumen">
          <span className="tarjeta-resumen-titulo">Movimientos</span>
          <strong className="tarjeta-resumen-numero">{movimientos.length}</strong>
          <small className="tarjeta-resumen-subtitulo">según los filtros</small>
        </div>
        <div className="tarjeta-resumen tarjeta-resumen-azul">
          <span className="tarjeta-resumen-titulo">Unidades que entraron</span>
          <strong className="tarjeta-resumen-numero">{unidades('ENTRADA').toLocaleString('es-CL')}</strong>
          <small className="tarjeta-resumen-subtitulo">por entradas con cotización</small>
        </div>
        <div className="tarjeta-resumen tarjeta-resumen-gris">
          <span className="tarjeta-resumen-titulo">Unidades que salieron</span>
          <strong className="tarjeta-resumen-numero">{unidades('SALIDA').toLocaleString('es-CL')}</strong>
          <small className="tarjeta-resumen-subtitulo">por salidas con QR</small>
        </div>
      </div>

      <div className="filtros filtros-acciones">
        <input
          type="search"
          placeholder="Buscar por producto o código"
          value={buscar}
          onChange={(e) => setBuscar(e.target.value)}
        />
        <select value={tipo} onChange={(e) => setTipo(e.target.value)} aria-label="Tipo">
          <option value="">Entradas y salidas</option>
          <option value="ENTRADA">Solo entradas</option>
          <option value="SALIDA">Solo salidas</option>
        </select>
        <input type="date" value={desde} onChange={(e) => setDesde(e.target.value)} aria-label="Desde" />
        <input type="date" value={hasta} onChange={(e) => setHasta(e.target.value)} aria-label="Hasta" />
        <button type="button" className="boton boton-secundario" onClick={limpiarFiltros}>
          Limpiar
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      <div className="tabla-contenedor">
        <table className="tabla">
          <thead>
            <tr>
              <th>Fecha</th>
              <th>Tipo</th>
              <th>Producto</th>
              <th>Cantidad</th>
              <th>Usuario</th>
              <th>Origen</th>
              <th>Observaciones</th>
            </tr>
          </thead>
          <tbody>
            {cargando && (
              <tr>
                <td colSpan="7" className="tabla-mensaje">Cargando movimientos...</td>
              </tr>
            )}

            {!cargando && movimientos.length === 0 && (
              <tr>
                <td colSpan="7" className="tabla-mensaje">No hay movimientos para estos filtros.</td>
              </tr>
            )}

            {!cargando &&
              movimientos.map((m) => (
                <tr key={m.id}>
                  <td className="sin-salto">{formatearFechaHora(m.fecha)}</td>
                  <td className="sin-salto">
                    <span className={`estado ${m.tipo === 'ENTRADA' ? 'estado-recibida' : 'estado-aprobada'}`}>
                      {m.tipo === 'ENTRADA' ? 'Entrada' : 'Salida'}
                    </span>
                  </td>
                  <td>
                    {m.producto_nombre} <span className="ayuda">{m.producto_codigo}</span>
                  </td>
                  <td className="sin-salto">
                    {m.tipo === 'ENTRADA' ? '+' : '−'}
                    {m.cantidad.toLocaleString('es-CL')}
                  </td>
                  <td>{m.usuario_nombre}</td>
                  <td className="sin-salto">{m.referencia}</td>
                  <td>{m.observaciones}</td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export default Movimientos;
