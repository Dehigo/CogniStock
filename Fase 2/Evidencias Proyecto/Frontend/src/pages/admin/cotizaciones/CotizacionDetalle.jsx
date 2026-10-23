import { useEffect, useState } from 'react';
import { obtenerTipoCambio } from '../../../services/api';
import EstadoCotizacion from './EstadoCotizacion';
import { formatearMonto } from './formato';

// Frankfurter no publica el peso chileno: solo se convierte entre USD y EUR.
const OTRA_MONEDA = { USD: 'EUR', EUR: 'USD' };

// Muestra una cotización que ya no se puede editar (aprobada, recibida o anulada).
function CotizacionDetalle({ token, cotizacion, onCerrar }) {
  const moneda = cotizacion.moneda_codigo;
  const otraMoneda = OTRA_MONEDA[moneda];
  const [cambio, setCambio] = useState(null);

  useEffect(() => {
    if (!otraMoneda) return;
    // Si la API falla, simplemente no se muestra la conversión (RB-008).
    obtenerTipoCambio(token, moneda, otraMoneda)
      .then(setCambio)
      .catch(() => {});
  }, [token, moneda, otraMoneda]);

  return (
    <div className="modal-fondo" onClick={onCerrar}>
      <div className="modal modal-grande" onClick={(e) => e.stopPropagation()}>
        <h3>
          Cotización {cotizacion.numero} <EstadoCotizacion estado={cotizacion.estado} />
        </h3>
        <p className="ayuda">
          {cotizacion.proveedor_nombre} · creada por {cotizacion.creado_por_nombre}
          {cotizacion.observaciones && ` · ${cotizacion.observaciones}`}
        </p>

        <div className="tabla-contenedor">
          <table className="tabla">
            <thead>
              <tr>
                <th>Producto</th>
                <th>Cotizado</th>
                <th>Recibido</th>
                <th>Pendiente</th>
                <th>Precio unitario</th>
              </tr>
            </thead>
            <tbody>
              {cotizacion.detalles.map((d) => (
                <tr key={d.id}>
                  <td>{d.producto_nombre}</td>
                  <td className="sin-salto">{d.cantidad}</td>
                  <td className="sin-salto">{d.cantidad_recibida}</td>
                  <td className="sin-salto">{d.cantidad_pendiente}</td>
                  <td className="sin-salto">{formatearMonto(d.precio_unitario, moneda)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="detalle-total">Total: {formatearMonto(cotizacion.total, moneda)}</p>
        {cambio && (
          <p className="ayuda detalle-total">
            Equivale a {formatearMonto(cotizacion.total * cambio.valor, otraMoneda)} (Frankfurter, {cambio.fecha})
          </p>
        )}

        <div className="modal-acciones">
          <button type="button" className="boton boton-secundario" onClick={onCerrar}>
            Cerrar
          </button>
        </div>
      </div>
    </div>
  );
}

export default CotizacionDetalle;
