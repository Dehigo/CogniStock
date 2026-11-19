import { useCallback, useEffect, useState } from 'react';
import {
  desactivarProducto,
  editarProducto,
  eliminarProducto,
  listarCategorias,
  listarProductos,
} from '../../../services/api';
import ProductoForm from './ProductoForm';
import QrProducto from './QrProducto';
import { ROL_ADMINISTRADOR, gestionaInventario } from '../secciones';

function formatearNumero(valor) {
  return Number(valor).toLocaleString('es-CL');
}

function formatearUnidades(cantidad) {
  return `${formatearNumero(cantidad)} ${cantidad === 1 ? 'unidad' : 'unidades'}`;
}

function estadoStock(producto) {
  const stock = Number(producto.stock_actual ?? 0);
  const minimo = Number(producto.stock_minimo ?? 0);

  if (!producto.activo) {
    return { etiqueta: 'Inactivo', clase: 'estado-inactivo' };
  }

  if (stock <= 0) {
    return { etiqueta: 'Agotado', clase: 'stock-agotado' };
  }

  if (stock < minimo) {
    return { etiqueta: 'Stock bajo', clase: 'stock-bajo' };
  }

  return { etiqueta: 'Disponible', clase: 'stock-disponible' };
}

// Íconos simples para las tarjetas de resumen
function Icono({ children }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {children}
    </svg>
  );
}

const ICONO_PRODUCTOS = (
  <Icono>
    <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
    <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
    <line x1="12" y1="22.08" x2="12" y2="12" />
  </Icono>
);

const ICONO_ACTIVOS = (
  <Icono>
    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
    <polyline points="22 4 12 14.01 9 11.01" />
  </Icono>
);

const ICONO_ALERTA = (
  <Icono>
    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
    <line x1="12" y1="9" x2="12" y2="13" />
    <line x1="12" y1="17" x2="12.01" y2="17" />
  </Icono>
);

function Productos({ token, usuarioActual }) {
  // El usuario operativo solo consulta productos; crear, editar y desactivar es del encargado (HU-03).
  const puedeEditar = gestionaInventario(usuarioActual.rol);
  const puedeEliminar = usuarioActual.rol === ROL_ADMINISTRADOR;
  const [productos, setProductos] = useState([]);
  const [categorias, setCategorias] = useState([]);
  const [buscar, setBuscar] = useState('');
  const [categoria, setCategoria] = useState('');
  const [estado, setEstado] = useState('');
  const [stockBajo, setStockBajo] = useState(false);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState('');
  const [formulario, setFormulario] = useState(null);
  const [productoQr, setProductoQr] = useState(null);

  const cargarProductos = useCallback(async () => {
    setCargando(true);
    setError('');
    try {
      setProductos(
        await listarProductos(token, {
          buscar,
          categoria,
          activo: estado,
          stock_bajo: stockBajo ? 'true' : '',
        }),
      );
    } catch (err) {
      setError(err.message);
    } finally {
      setCargando(false);
    }
  }, [token, buscar, categoria, estado, stockBajo]);

  useEffect(() => {
    const espera = setTimeout(cargarProductos, 300);
    return () => clearTimeout(espera);
  }, [cargarProductos]);

  useEffect(() => {
    listarCategorias(token).then(setCategorias).catch((err) => setError(err.message));
  }, [token]);

  async function cambiarEstado(producto) {
    const accion = producto.activo ? 'desactivar' : 'reactivar';
    if (!window.confirm(`¿Seguro que quieres ${accion} ${producto.nombre}?`)) return;

    try {
      if (producto.activo) {
        await desactivarProducto(token, producto.id);
      } else {
        await editarProducto(token, producto.id, { activo: true });
      }
      cargarProductos();
    } catch (err) {
      setError(err.message);
    }
  }

  async function eliminarDefinitivo(producto) {
    if (!window.confirm(`¿Seguro que quieres eliminar permanentemente ${producto.nombre}? Esta acción no se puede deshacer.`)) return;

    try {
      await eliminarProducto(token, producto.id);
      await cargarProductos();
    } catch (err) {
      setError(err.message);
    }
  }

  function alGuardar() {
    setFormulario(null);
    cargarProductos();
  }

  function limpiarFiltros() {
    setBuscar('');
    setCategoria('');
    setEstado('');
    setStockBajo(false);
  }

  const resumen = {
    total: productos.length,
    activos: productos.filter((producto) => producto.activo).length,
    bajo: productos.filter((producto) => Number(producto.stock_actual ?? 0) < Number(producto.stock_minimo ?? 0)).length,
  };

  return (
    <section>
      <div className="seccion-cabecera">
        <h2>Productos</h2>
        {puedeEditar && (
          <button className="boton" onClick={() => setFormulario({ producto: null })}>
            + Nuevo producto
          </button>
        )}
      </div>

      <div className="resumen-grid">
        <div className="tarjeta-resumen tarjeta-resumen-azul">
          <div className="tarjeta-resumen-header">
            <span className="tarjeta-resumen-icon">{ICONO_PRODUCTOS}</span>
            <span className="tarjeta-resumen-titulo">Total</span>
          </div>
          <div className="tarjeta-resumen-body">
            <span className="tarjeta-resumen-numero">{resumen.total}</span>
            <span className="tarjeta-resumen-subtitulo">Productos registrados</span>
          </div>
        </div>
        <div className="tarjeta-resumen tarjeta-resumen-verde">
          <div className="tarjeta-resumen-header">
            <span className="tarjeta-resumen-icon">{ICONO_ACTIVOS}</span>
            <span className="tarjeta-resumen-titulo">Activos</span>
          </div>
          <div className="tarjeta-resumen-body">
            <span className="tarjeta-resumen-numero">{resumen.activos}</span>
            <span className="tarjeta-resumen-subtitulo">Disponibles en operación</span>
          </div>
        </div>
        <div className="tarjeta-resumen tarjeta-resumen-rojo">
          <div className="tarjeta-resumen-header">
            <span className="tarjeta-resumen-icon">{ICONO_ALERTA}</span>
            <span className="tarjeta-resumen-titulo">Stock bajo</span>
          </div>
          <div className="tarjeta-resumen-body">
            <span className="tarjeta-resumen-numero">{resumen.bajo}</span>
            <span className="tarjeta-resumen-subtitulo">Requieren atención</span>
          </div>
        </div>
      </div>

      <div className="filtros filtros-acciones">
        <input
          type="search"
          placeholder="Buscar por nombre o código"
          aria-label="Buscar productos"
          value={buscar}
          onChange={(e) => setBuscar(e.target.value)}
        />
        <select value={categoria} onChange={(e) => setCategoria(e.target.value)} aria-label="Categoría">
          <option value="">Todas las categorías</option>
          {categorias.map((c) => (
            <option key={c.id} value={c.id}>
              {c.nombre}
            </option>
          ))}
        </select>
        <select value={estado} onChange={(e) => setEstado(e.target.value)} aria-label="Estado">
          <option value="">Todos los estados</option>
          <option value="true">Activos</option>
          <option value="false">Inactivos</option>
        </select>
        <button
          type="button"
          className={`boton boton-chip ${stockBajo ? 'boton-chip-activo' : ''}`}
          onClick={() => setStockBajo((actual) => !actual)}
        >
          {stockBajo ? 'Ver todos' : 'Solo stock bajo'}
        </button>
        <button type="button" className="boton boton-secundario" onClick={limpiarFiltros}>
          Limpiar
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      <div className="tabla-contenedor">
        <table className="tabla">
          <thead>
            <tr>
              <th>Código</th>
              <th>Nombre</th>
              <th>Categoría</th>
              <th>Unidad</th>
              <th>Stock</th>
              <th>Precio ref.</th>
              <th>Estado</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {cargando && (
              <tr>
                <td colSpan="8" className="tabla-mensaje">Cargando productos...</td>
              </tr>
            )}

            {!cargando && productos.length === 0 && (
              <tr>
                <td colSpan="8" className="tabla-mensaje">No se encontraron productos.</td>
              </tr>
            )}

            {!cargando &&
              productos.map((producto) => {
                const stock = Number(producto.stock_actual ?? 0);
                const valorEstado = estadoStock(producto);
                const filaInactiva = !producto.activo ? 'fila-inactiva' : '';
                return (
                  <tr key={producto.id} className={filaInactiva}>
                    <td data-label="Código" className="sin-salto">
                      <span className="codigo-producto">{producto.codigo}</span>
                    </td>
                    <td data-label="Nombre">{producto.nombre}</td>
                    <td data-label="Categoría">{producto.categoria_nombre ?? 'Sin categoría'}</td>
                    <td data-label="Unidad" className="sin-salto">{producto.unidad_medida ?? 'unidad'}</td>
                    <td data-label="Stock" className="sin-salto">
                      {formatearUnidades(stock)}
                      <span className="celda-secundaria">Mínimo {formatearNumero(producto.stock_minimo ?? 0)}</span>
                    </td>
                    <td data-label="Precio ref." className="sin-salto">${formatearNumero(producto.precio_referencia)}</td>
                    <td data-label="Estado" className="sin-salto">
                      <span className={`stock-insignia ${valorEstado.clase}`}>{valorEstado.etiqueta}</span>
                    </td>
                    <td className="tabla-acciones">
                      <button className="boton-enlace" onClick={() => setProductoQr(producto)}>
                        QR
                      </button>
                      <button
                        className="boton-enlace"
                        onClick={() => {
                          const codigoQr = encodeURIComponent(producto.codigo_qr || producto.codigo || '');
                          window.location.hash = `#salidas?codigo_qr=${codigoQr}`;
                        }}
                      >
                        Salida
                      </button>
                      {puedeEditar && (
                        <>
                          <button className="boton-enlace" onClick={() => setFormulario({ producto })}>
                            Editar
                          </button>
                          <button className="boton-enlace" onClick={() => cambiarEstado(producto)}>
                            {producto.activo ? 'Desactivar' : 'Reactivar'}
                          </button>
                          {puedeEliminar && (
                            <button className="boton-enlace boton-enlace-peligro" onClick={() => eliminarDefinitivo(producto)}>
                              Eliminar
                            </button>
                          )}
                        </>
                      )}
                    </td>
                  </tr>
                );
              })}
          </tbody>
        </table>
      </div>

      {formulario && (
        <ProductoForm
          token={token}
          producto={formulario.producto}
          categorias={categorias}
          onGuardar={alGuardar}
          onCancelar={() => setFormulario(null)}
        />
      )}

      {productoQr && <QrProducto producto={productoQr} onCerrar={() => setProductoQr(null)} />}
    </section>
  );
}

export default Productos;