import { useEffect, useState } from 'react';
import {
  crearCotizacion,
  editarCotizacion,
  listarMonedas,
  listarProductos,
  listarProveedores,
} from '../../../services/api';
import EstadoCotizacion from './EstadoCotizacion';
import { formatearMonto } from './formato';

const FILA_VACIA = { producto: '', cantidad: 1, precio_unitario: 0 };

function hoy() {
  const ahora = new Date();
  return new Date(ahora.getTime() - ahora.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
}

function CotizacionForm({ token, cotizacion, onGuardar, onCancelar }) {
  const esNueva = cotizacion === null;
  const soloLectura = !esNueva && cotizacion.estado !== 'REGISTRADA';
  const [numero, setNumero] = useState(cotizacion?.numero ?? '');
  const [proveedor, setProveedor] = useState(cotizacion?.proveedor ?? '');
  const [moneda, setMoneda] = useState(cotizacion?.moneda ?? '');
  const [fecha, setFecha] = useState(cotizacion?.fecha ?? hoy());
  const [observaciones, setObservaciones] = useState(cotizacion?.observaciones ?? '');
  const [detalles, setDetalles] = useState(
    cotizacion?.detalles.map(({ producto, cantidad, precio_unitario }) => ({ producto, cantidad, precio_unitario })) ?? [
      { ...FILA_VACIA },
    ],
  );
  const [proveedores, setProveedores] = useState([]);
  const [productos, setProductos] = useState([]);
  const [monedas, setMonedas] = useState([]);
  const [error, setError] = useState('');
  const [guardando, setGuardando] = useState(false);

  useEffect(() => {
    if (soloLectura) return;
    Promise.all([
      listarProveedores(token, { activo: 'true' }),
      listarProductos(token, { activo: 'true' }),
      listarMonedas(token),
    ])
      .then(([listaProveedores, listaProductos, listaMonedas]) => {
        setProveedores(listaProveedores);
        setProductos(listaProductos);
        setMonedas(listaMonedas);
        setMoneda((actual) => actual || listaMonedas.find((m) => m.codigo === 'CLP')?.id || '');
      })
      .catch((err) => setError(err.message));
  }, [token, soloLectura]);

  const codigoMoneda = soloLectura
    ? cotizacion.moneda_codigo
    : (monedas.find((m) => m.id === Number(moneda))?.codigo ?? 'CLP');
  const total = detalles.reduce((suma, d) => suma + Number(d.cantidad || 0) * Number(d.precio_unitario || 0), 0);

  function cambiarFila(indice, campo, valor) {
    setDetalles((actuales) => actuales.map((fila, i) => (i === indice ? { ...fila, [campo]: valor } : fila)));
  }

  function elegirProducto(indice, valor) {
    const elegido = productos.find((p) => p.id === Number(valor));
    setDetalles((actuales) =>
      actuales.map((fila, i) =>
        i === indice
          ? { ...fila, producto: valor, precio_unitario: fila.precio_unitario || elegido?.precio_referencia || 0 }
          : fila,
      ),
    );
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError('');
    setGuardando(true);

    const datos = {
      numero,
      proveedor: Number(proveedor),
      moneda: Number(moneda),
      fecha,
      observaciones,
      detalles: detalles.map((d) => ({
        producto: Number(d.producto),
        cantidad: Number(d.cantidad),
        precio_unitario: Number(d.precio_unitario),
      })),
    };

    try {
      if (esNueva) {
        await crearCotizacion(token, datos);
      } else {
        await editarCotizacion(token, cotizacion.id, datos);
      }
      onGuardar();
    } catch (err) {
      setError(err.message);
    } finally {
      setGuardando(false);
    }
  }

  if (soloLectura) {
    return (
      <div className="modal-fondo" onClick={onCancelar}>
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
                    <td className="sin-salto">{formatearMonto(d.precio_unitario, codigoMoneda)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="detalle-total">Total: {formatearMonto(cotizacion.total, codigoMoneda)}</p>

          <div className="modal-acciones">
            <button type="button" className="boton boton-secundario" onClick={onCancelar}>
              Cerrar
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="modal-fondo" onClick={onCancelar}>
      <form className="modal modal-grande" onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
        <h3>{esNueva ? 'Nueva cotización' : `Editar ${cotizacion.numero}`}</h3>

        <div className="fila-doble">
          <div>
            <label htmlFor="numero">Número</label>
            <input
              id="numero"
              value={numero}
              onChange={(e) => setNumero(e.target.value)}
              placeholder="N° de la cotización del proveedor"
              required
            />
          </div>
          <div>
            <label htmlFor="proveedor">Proveedor</label>
            <select id="proveedor" value={proveedor} onChange={(e) => setProveedor(e.target.value)} required>
              <option value="">Selecciona un proveedor</option>
              {proveedores.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.nombre}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="fila-doble">
          <div>
            <label htmlFor="moneda">Moneda</label>
            <select id="moneda" value={moneda} onChange={(e) => setMoneda(e.target.value)} required>
              {monedas.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.codigo} · {m.nombre}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="fecha">Fecha</label>
            <input id="fecha" type="date" value={fecha} onChange={(e) => setFecha(e.target.value)} required />
          </div>
        </div>

        <label>Productos cotizados</label>
        <div className="detalle-fila ayuda">
          <span>Producto</span>
          <span>Cantidad</span>
          <span>Precio unitario</span>
          <span></span>
        </div>
        {detalles.map((fila, indice) => (
          <div className="detalle-fila" key={indice}>
            <select
              value={fila.producto}
              onChange={(e) => elegirProducto(indice, e.target.value)}
              aria-label="Producto"
              required
            >
              <option value="">Selecciona un producto</option>
              {productos.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.codigo} · {p.nombre}
                </option>
              ))}
            </select>
            <input
              type="number"
              min="1"
              value={fila.cantidad}
              onChange={(e) => cambiarFila(indice, 'cantidad', e.target.value)}
              aria-label="Cantidad"
              required
            />
            <input
              type="number"
              min="0"
              step="0.01"
              value={fila.precio_unitario}
              onChange={(e) => cambiarFila(indice, 'precio_unitario', e.target.value)}
              aria-label="Precio unitario"
              required
            />
            <button
              type="button"
              className="boton-enlace"
              onClick={() => setDetalles((actuales) => actuales.filter((_, i) => i !== indice))}
              disabled={detalles.length === 1}
            >
              Quitar
            </button>
          </div>
        ))}
        <button
          type="button"
          className="boton boton-secundario"
          onClick={() => setDetalles((actuales) => [...actuales, { ...FILA_VACIA }])}
        >
          + Agregar producto
        </button>
        <p className="detalle-total">Total: {formatearMonto(total, codigoMoneda)}</p>

        <label htmlFor="observaciones">Observaciones</label>
        <textarea id="observaciones" rows="2" value={observaciones} onChange={(e) => setObservaciones(e.target.value)} />

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

export default CotizacionForm;
