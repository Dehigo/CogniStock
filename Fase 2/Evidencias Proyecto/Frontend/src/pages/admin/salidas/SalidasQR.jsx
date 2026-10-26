import { useState } from 'react';
import { buscarProductoPorQr, registrarSalidaQr } from '../../../services/api';
import QrScanner from '../../../components/QrScanner';

function formatearNumero(valor) {
  return Number(valor ?? 0).toLocaleString('es-CL');
}

function formatearUnidades(cantidad) {
  return `${formatearNumero(cantidad)} ${cantidad === 1 ? 'unidad' : 'unidades'}`;
}

function SalidasQR({ token }) {
  const [codigoQr, setCodigoQr] = useState('');
  const [producto, setProducto] = useState(null);
  const [cantidad, setCantidad] = useState(1);
  const [observaciones, setObservaciones] = useState('');
  const [cargando, setCargando] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState('');
  const [mensaje, setMensaje] = useState('');
  const [mostrarCamara, setMostrarCamara] = useState(false);

  async function buscarProducto(event) {
    if (event) event.preventDefault();
    const codigo = codigoQr.trim();

    if (!codigo) {
      setProducto(null);
      setError('Ingresa un código QR para consultar el producto.');
      return;
    }

    setCargando(true);
    setError('');
    setMensaje('');

    try {
      const datos = await buscarProductoPorQr(token, codigo);
      setProducto(datos);
      setCantidad(1);
      setObservaciones('');
    } catch (err) {
      setProducto(null);
      setError(err.message);
    } finally {
      setCargando(false);
    }
  }

  async function handleScanSuccess(decodedText) {
    setCodigoQr(decodedText);
    setMostrarCamara(false); 
    
    const codigo = decodedText.trim();
    setCargando(true);
    setError('');
    setMensaje('');

    try {
      const datos = await buscarProductoPorQr(token, codigo);
      setProducto(datos);
      setCantidad(1);
      setObservaciones('');
    } catch (err) {
      setProducto(null);
      setError(err.message);
    } finally {
      setCargando(false);
    }
  }

  async function registrarSalida(event) {
    event.preventDefault();

    if (!producto) {
      setError('Primero busca un producto válido.');
      return;
    }

    const cantidadSalida = Number(cantidad);
    if (!Number.isInteger(cantidadSalida) || cantidadSalida <= 0) {
      setError('La cantidad debe ser un entero mayor que 0.');
      return;
    }

    const stockDisponible = Number(producto.stock_actual ?? 0);
    if (cantidadSalida > stockDisponible) {
      setError(`Stock insuficiente para esta salida. Disponible: ${formatearUnidades(stockDisponible)}.`);
      return;
    }

    setEnviando(true);
    setError('');
    setMensaje('');

    try {
      const respuesta = await registrarSalidaQr(token, {
        codigo_qr: producto.codigo_qr,
        cantidad: cantidadSalida,
        observaciones,
      });

      setMensaje(`${respuesta.detail} Quedan ${formatearUnidades(respuesta.stock_restante ?? 0)} en stock.`);
      setCodigoQr('');
      setProducto(null);
      setCantidad(1);
      setObservaciones('');
    } catch (err) {
      setError(err.message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <section>
      <div className="seccion-cabecera">
        <h2>Salidas (QR)</h2>
        <span className="insignia insignia-base">RF-08 / HU-04</span>
      </div>

      <form onSubmit={buscarProducto} className="filtros filtros-acciones" style={{ marginBottom: '12px', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
        <input
          type="text"
          value={codigoQr}
          onChange={(event) => setCodigoQr(event.target.value)}
          placeholder="Escanea o escribe el código QR"
          aria-label="Código QR del producto"
          style={{ flex: 1, minWidth: '200px' }}
        />
        <button type="submit" className="boton" disabled={cargando}>
          {cargando ? 'Buscando...' : 'Buscar producto'}
        </button>
        <button 
          type="button" 
          className="boton boton-secundario" 
          onClick={() => setMostrarCamara(!mostrarCamara)}
        >
          {mostrarCamara ? 'Cerrar Cámara' : '📷 Usar Cámara'}
        </button>
      </form>

      {mostrarCamara && (
        <div style={{ 
          marginBottom: '16px', 
          background: '#1e293b', 
          border: '1px solid #334155',
          padding: '16px', 
          borderRadius: '12px',
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.3)',
          color: '#f8fafc'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <p style={{ margin: 0, fontWeight: '600', fontSize: '0.95rem' }}>📷 Escanea el código QR del producto</p>
            <button 
              type="button" 
              className="boton boton-secundario" 
              style={{ padding: '4px 10px', fontSize: '0.85rem' }}
              onClick={() => setMostrarCamara(false)}
            >
              ✕ Cerrar
            </button>
          </div>
          
          <div style={{ 
            overflow: 'hidden', 
            borderRadius: '8px', 
            background: '#0f172a',
            border: '1px solid #334155'
          }}>
            <QrScanner onScanSuccess={handleScanSuccess} />
          </div>
        </div>
      )}

      {error && <p className="error">{error}</p>}
      {mensaje && <p className="success">{mensaje}</p>}

      {producto && (
        <div className="tarjeta-resumen tarjeta-resumen-azul" style={{ marginTop: '16px' }}>
          <span className="tarjeta-resumen-titulo">Producto identificado</span>
          <div className="fila-doble" style={{ marginTop: '12px' }}>
            <div>
              <strong>{producto.nombre}</strong>
              <div className="ayuda">Código: {producto.codigo}</div>
            </div>
            <div>
              <strong>Stock actual</strong>
              <div className="ayuda">{formatearUnidades(Number(producto.stock_actual ?? 0))}</div>
            </div>
          </div>

          <div className="fila-doble" style={{ marginTop: '12px' }}>
            <div>
              <strong>QR</strong>
              <div className="ayuda">{producto.codigo_qr}</div>
            </div>
            <div>
              <strong>Categoría</strong>
              <div className="ayuda">{producto.categoria_nombre || 'Sin categoría'}</div>
            </div>
          </div>

          <form onSubmit={registrarSalida} style={{ marginTop: '20px' }}>
            <div className="fila-doble">
              <div>
                <label htmlFor="cantidad-salida">Cantidad a retirar</label>
                <input
                  id="cantidad-salida"
                  type="number"
                  min="1"
                  value={cantidad}
                  onChange={(event) => setCantidad(event.target.value)}
                />
              </div>
              <div>
                <label htmlFor="stock-disp">Stock disponible</label>
                <input id="stock-disp" type="text" value={formatearUnidades(Number(producto.stock_actual ?? 0))} readOnly />
              </div>
            </div>

            <label htmlFor="observaciones-salida">Observaciones</label>
            <textarea
              id="observaciones-salida"
              rows="3"
              value={observaciones}
              onChange={(event) => setObservaciones(event.target.value)}
              placeholder="Ej.: Ajuste por venta del día, retiro por despacho, etc."
            />

            <div className="modal-acciones">
              <button type="button" className="boton boton-secundario" onClick={() => setProducto(null)}>
                Cancelar
              </button>
              <button type="submit" className="boton" disabled={enviando}>
                {enviando ? 'Registrando salida...' : 'Registrar salida'}
              </button>
            </div>
          </form>
        </div>
      )}
    </section>
  );
}

export default SalidasQR;