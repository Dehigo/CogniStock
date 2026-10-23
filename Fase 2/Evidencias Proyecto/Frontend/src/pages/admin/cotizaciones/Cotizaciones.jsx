import { useCallback, useEffect, useState } from 'react';
import { cambiarEstadoCotizacion, listarCotizaciones } from '../../../services/api';
import CotizacionDetalle from './CotizacionDetalle';
import CotizacionForm from './CotizacionForm';
import EstadoCotizacion from './EstadoCotizacion';
import { formatearFecha, formatearMonto } from './formato';

const ESTADOS = ['REGISTRADA', 'APROBADA', 'RECIBIDA', 'ANULADA'];

function Cotizaciones({ token }) {
  const [cotizaciones, setCotizaciones] = useState([]);
  const [buscar, setBuscar] = useState('');
  const [estado, setEstado] = useState('');
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState('');
  const [formulario, setFormulario] = useState(null);

  // Una cotización ya aprobada, recibida o anulada solo se puede ver, no editar.
  const soloVer = formulario?.cotizacion && formulario.cotizacion.estado !== 'REGISTRADA';
  const contar = (codigo) => cotizaciones.filter((cotizacion) => cotizacion.estado === codigo).length;

  const cargarCotizaciones = useCallback(async () => {
    try {
      setCotizaciones(await listarCotizaciones(token, { buscar, estado }));
      setError('');
    } catch (err) {
      setError(err.message);
    } finally {
      setCargando(false);
    }
  }, [token, buscar, estado]);

  useEffect(() => {
    const espera = setTimeout(cargarCotizaciones, 300);
    return () => clearTimeout(espera);
  }, [cargarCotizaciones]);

  async function cambiarEstado(cotizacion, nuevoEstado) {
    const accion = nuevoEstado === 'APROBADA' ? 'aprobar' : 'anular';
    let motivo = '';
    if (nuevoEstado === 'ANULADA') {
      motivo = window.prompt(`Motivo para anular ${cotizacion.numero}:`);
      if (motivo === null) return;
    } else if (!window.confirm(`¿Seguro que quieres ${accion} la cotización ${cotizacion.numero}?`)) {
      return;
    }

    try {
      await cambiarEstadoCotizacion(token, cotizacion.id, nuevoEstado, motivo);
      cargarCotizaciones();
    } catch (err) {
      setError(err.message);
    }
  }

  function alGuardar() {
    setFormulario(null);
    cargarCotizaciones();
  }

  return (
    <section>
      <div className="seccion-cabecera">
        <h2>Cotizaciones</h2>
        <button className="boton" onClick={() => setFormulario({ cotizacion: null })}>
          Nueva cotización
        </button>
      </div>

      <div className="resumen-grid">
        <div className="tarjeta-resumen">
          <span className="tarjeta-resumen-titulo">Registradas</span>
          <strong className="tarjeta-resumen-numero">{contar('REGISTRADA')}</strong>
          <small className="tarjeta-resumen-subtitulo">esperan aprobación</small>
        </div>
        <div className="tarjeta-resumen tarjeta-resumen-azul">
          <span className="tarjeta-resumen-titulo">Aprobadas</span>
          <strong className="tarjeta-resumen-numero">{contar('APROBADA')}</strong>
          <small className="tarjeta-resumen-subtitulo">permiten registrar entradas</small>
        </div>
        <div className="tarjeta-resumen tarjeta-resumen-gris">
          <span className="tarjeta-resumen-titulo">Recibidas</span>
          <strong className="tarjeta-resumen-numero">{contar('RECIBIDA')}</strong>
          <small className="tarjeta-resumen-subtitulo">ingresadas por completo</small>
        </div>
      </div>

      <div className="filtros">
        <input
          type="search"
          placeholder="Buscar por número o proveedor"
          value={buscar}
          onChange={(e) => setBuscar(e.target.value)}
        />
        <select value={estado} onChange={(e) => setEstado(e.target.value)} aria-label="Estado">
          <option value="">Todos los estados</option>
          {ESTADOS.map((codigo) => (
            <option key={codigo} value={codigo}>
              {codigo}
            </option>
          ))}
        </select>
      </div>

      {error && <p className="error">{error}</p>}

      <div className="tabla-contenedor">
        <table className="tabla">
          <thead>
            <tr>
              <th>Número</th>
              <th>Proveedor</th>
              <th>Fecha</th>
              <th>Productos</th>
              <th>Total</th>
              <th>Estado</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {cargando && (
              <tr>
                <td colSpan="7" className="tabla-mensaje">Cargando cotizaciones...</td>
              </tr>
            )}

            {!cargando && cotizaciones.length === 0 && (
              <tr>
                <td colSpan="7" className="tabla-mensaje">No se encontraron cotizaciones.</td>
              </tr>
            )}

            {!cargando &&
              cotizaciones.map((cotizacion) => (
                <tr key={cotizacion.id} className={cotizacion.estado === 'ANULADA' ? 'fila-inactiva' : ''}>
                  <td className="sin-salto">{cotizacion.numero}</td>
                  <td>{cotizacion.proveedor_nombre}</td>
                  <td className="sin-salto">{formatearFecha(cotizacion.fecha)}</td>
                  <td className="sin-salto">{cotizacion.detalles.length}</td>
                  <td className="sin-salto">{formatearMonto(cotizacion.total, cotizacion.moneda_codigo)}</td>
                  <td className="sin-salto">
                    <EstadoCotizacion estado={cotizacion.estado} />
                  </td>
                  <td className="tabla-acciones">
                    <button className="boton-enlace" onClick={() => setFormulario({ cotizacion })}>
                      {cotizacion.estado === 'REGISTRADA' ? 'Editar' : 'Ver'}
                    </button>
                    {cotizacion.estado === 'REGISTRADA' && (
                      <button className="boton-enlace" onClick={() => cambiarEstado(cotizacion, 'APROBADA')}>
                        Aprobar
                      </button>
                    )}
                    {cotizacion.estado === 'APROBADA' && (
                      <a className="boton-enlace" href="#entradas">
                        Registrar entrada
                      </a>
                    )}
                    {['REGISTRADA', 'APROBADA'].includes(cotizacion.estado) && (
                      <button className="boton-enlace" onClick={() => cambiarEstado(cotizacion, 'ANULADA')}>
                        Anular
                      </button>
                    )}
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      {formulario && !soloVer && (
        <CotizacionForm
          token={token}
          cotizacion={formulario.cotizacion}
          onGuardar={alGuardar}
          onCancelar={() => setFormulario(null)}
        />
      )}
      {soloVer && <CotizacionDetalle token={token} cotizacion={formulario.cotizacion} onCerrar={() => setFormulario(null)} />}
    </section>
  );
}

export default Cotizaciones;
