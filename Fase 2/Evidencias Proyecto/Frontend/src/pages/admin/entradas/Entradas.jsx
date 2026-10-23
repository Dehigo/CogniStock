import { useCallback, useEffect, useState } from 'react';
import { listarCotizaciones, listarEntradas, registrarEntrada } from '../../../services/api';

function formatearFechaHora(fecha) {
  return new Date(fecha).toLocaleString('es-CL', { dateStyle: 'short', timeStyle: 'short' });
}

function Entradas({ token }) {
  const [cotizaciones, setCotizaciones] = useState([]);
  const [entradas, setEntradas] = useState([]);
  const [cotizacionId, setCotizacionId] = useState('');
  const [cantidades, setCantidades] = useState({});
  const [observaciones, setObservaciones] = useState('');
  const [cargando, setCargando] = useState(true);
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState('');
  const [mensaje, setMensaje] = useState('');

  const cotizacion = cotizaciones.find((c) => c.id === Number(cotizacionId));

  const cargarDatos = useCallback(
    () =>
      Promise.all([listarCotizaciones(token, { permite_entrada: 'true' }), listarEntradas(token)])
        .then(([aprobadas, recientes]) => {
          setCotizaciones(aprobadas);
          setEntradas(recientes);
        })
        .catch((err) => setError(err.message))
        .finally(() => setCargando(false)),
    [token],
  );

  useEffect(() => {
    cargarDatos();
  }, [cargarDatos]);

  function elegirCotizacion(id) {
    setCotizacionId(id);
    setError('');
    setMensaje('');
    const elegida = cotizaciones.find((c) => c.id === Number(id));
    // Por defecto se propone recibir todo lo que falta.
    setCantidades(Object.fromEntries((elegida?.detalles ?? []).map((d) => [d.producto, d.cantidad_pendiente])));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    const detalles = Object.entries(cantidades)
      .filter(([, cantidad]) => Number(cantidad) > 0)
      .map(([producto, cantidad]) => ({ producto: Number(producto), cantidad: Number(cantidad) }));

    if (detalles.length === 0) {
      setError('Indica al menos una cantidad recibida.');
      return;
    }

    setEnviando(true);
    setError('');
    setMensaje('');
    try {
      const entrada = await registrarEntrada(token, { cotizacion: cotizacion.id, detalles, observaciones });
      const unidades = entrada.detalles.reduce((suma, d) => suma + d.cantidad, 0);
      setMensaje(`Entrada #${entrada.id} registrada: ${unidades} unidades sumadas al stock.`);
      setCotizacionId('');
      setCantidades({});
      setObservaciones('');
      cargarDatos();
    } catch (err) {
      setError(err.message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <section>
      <div className="seccion-cabecera">
        <h2>Entradas</h2>
      </div>

      <p className="ayuda">Solo se puede registrar una entrada contra una cotización aprobada (RB-001, RB-002).</p>

      <div className="filtros">
        <select value={cotizacionId} onChange={(e) => elegirCotizacion(e.target.value)} aria-label="Cotización">
          <option value="">
            {cotizaciones.length === 0 && !cargando ? 'No hay cotizaciones aprobadas' : 'Selecciona una cotización aprobada'}
          </option>
          {cotizaciones.map((c) => (
            <option key={c.id} value={c.id}>
              {c.numero} · {c.proveedor_nombre}
            </option>
          ))}
        </select>
      </div>

      {error && <p className="error">{error}</p>}
      {mensaje && <p className="success">{mensaje}</p>}

      {cotizacion && (
        <form onSubmit={handleSubmit}>
          <div className="tabla-contenedor">
            <table className="tabla">
              <thead>
                <tr>
                  <th>Producto</th>
                  <th>Cotizado</th>
                  <th>Recibido</th>
                  <th>Pendiente</th>
                  <th>Cantidad que llega</th>
                </tr>
              </thead>
              <tbody>
                {cotizacion.detalles.map((d) => (
                  <tr key={d.producto} className={d.cantidad_pendiente === 0 ? 'fila-inactiva' : ''}>
                    <td>{d.producto_nombre}</td>
                    <td className="sin-salto">{d.cantidad}</td>
                    <td className="sin-salto">{d.cantidad_recibida}</td>
                    <td className="sin-salto">{d.cantidad_pendiente}</td>
                    <td>
                      <input
                        type="number"
                        min="0"
                        max={d.cantidad_pendiente}
                        value={cantidades[d.producto] ?? 0}
                        onChange={(e) => setCantidades((actuales) => ({ ...actuales, [d.producto]: e.target.value }))}
                        disabled={d.cantidad_pendiente === 0}
                        aria-label={`Cantidad de ${d.producto_nombre}`}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="filtros filtros-acciones">
            <input
              value={observaciones}
              onChange={(e) => setObservaciones(e.target.value)}
              placeholder="Observaciones (guía de despacho, estado de la mercadería...)"
              aria-label="Observaciones"
            />
            <button type="submit" className="boton" disabled={enviando}>
              {enviando ? 'Registrando...' : 'Registrar entrada'}
            </button>
          </div>
        </form>
      )}

      <h3>Últimas entradas</h3>
      <div className="tabla-contenedor">
        <table className="tabla">
          <thead>
            <tr>
              <th>Fecha</th>
              <th>Cotización</th>
              <th>Proveedor</th>
              <th>Productos</th>
              <th>Registrada por</th>
            </tr>
          </thead>
          <tbody>
            {cargando && (
              <tr>
                <td colSpan="5" className="tabla-mensaje">Cargando entradas...</td>
              </tr>
            )}

            {!cargando && entradas.length === 0 && (
              <tr>
                <td colSpan="5" className="tabla-mensaje">Todavía no hay entradas registradas.</td>
              </tr>
            )}

            {!cargando &&
              entradas.map((entrada) => (
                <tr key={entrada.id}>
                  <td className="sin-salto">{formatearFechaHora(entrada.fecha)}</td>
                  <td className="sin-salto">{entrada.cotizacion_numero}</td>
                  <td>{entrada.proveedor_nombre}</td>
                  <td>{entrada.detalles.map((d) => `${d.producto_nombre} × ${d.cantidad}`).join(', ')}</td>
                  <td>{entrada.usuario_nombre}</td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export default Entradas;
