import { useCallback, useEffect, useState } from 'react';
import { desactivarProducto, editarProducto, listarCategorias, listarProductos } from '../../../services/api';
import ProductoForm from './ProductoForm';
import QrProducto from './QrProducto';

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

function Productos({ token }) {
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
        <button className="boton" onClick={() => setFormulario({ producto: null })}>
          + Nuevo producto
        </button>
      </div>

      <div className="resumen-grid" style={{ marginBottom: '18px' }}>
        <div className="tarjeta-resumen tarjeta-resumen-azul">
          <span className="tarjeta-resumen-titulo">Total</span>
          <span className="tarjeta-resumen-numero">{resumen.total}</span>
          <span className="tarjeta-resumen-subtitulo">Productos registrados</span>
        </div>
        <div className="tarjeta-resumen tarjeta-resumen-gris">
          <span className="tarjeta-resumen-titulo">Activos</span>
          <span className="tarjeta-resumen-numero">{resumen.activos}</span>
          <span className="tarjeta-resumen-subtitulo">Disponibles en operación</span>
        </div>
        <div className="tarjeta-resumen tarjeta-resumen-gris">
          <span className="tarjeta-resumen-titulo">Stock bajo</span>
          <span className="tarjeta-resumen-numero">{resumen.bajo}</span>
          <span className="tarjeta-resumen-subtitulo">Requieren atención</span>
        </div>
      </div>

      <div className="filtros filtros-acciones">
        <input
          type="search"
          placeholder="Buscar por nombre o código"
          value={buscar}
          onChange={(e) => setBuscar(e.target.value)}
        />
        <select value={categoria} onChange={(e) => setCategoria(e.target.value)}>
          <option value="">Todas las categorías</option>
          {categorias.map((c) => (
            <option key={c.id} value={c.id}>
              {c.nombre}
            </option>
          ))}
        </select>
        <select value={estado} onChange={(e) => setEstado(e.target.value)}>
          <option value="">Todos</option>
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
              <th>Stock mínimo</th>
              <th>Precio ref.</th>
              <th>Estado</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {cargando && (
              <tr>
                <td colSpan="9" className="tabla-mensaje">Cargando productos...</td>
              </tr>
            )}

            {!cargando && productos.length === 0 && (
              <tr>
                <td colSpan="9" className="tabla-mensaje">No se encontraron productos.</td>
              </tr>
            )}

            {!cargando &&
              productos.map((producto) => {
                const stock = Number(producto.stock_actual ?? 0);
                const valorEstado = estadoStock(producto);
                const filaInactiva = !producto.activo ? 'fila-inactiva' : '';
                return (
                  <tr key={producto.id} className={filaInactiva}>
                    <td className="sin-salto">{producto.codigo}</td>
                    <td>{producto.nombre}</td>
                    <td>{producto.categoria_nombre ?? 'Sin categoría'}</td>
                    <td className="sin-salto">{producto.unidad_medida ?? 'unidad'}</td>
                    <td className="sin-salto">
                      <span className={`stock-insignia ${valorEstado.clase}`}>
                        {formatearUnidades(stock)}
                      </span>
                    </td>
                    <td className="sin-salto">{formatearNumero(producto.stock_minimo ?? 0)}</td>
                    <td className="sin-salto">${formatearNumero(producto.precio_referencia)}</td>
                    <td className="sin-salto">
                      <span className={`estado ${producto.activo ? 'estado-activo' : 'estado-inactivo'}`}>
                        {producto.activo ? 'Activo' : 'Inactivo'}
                      </span>
                      <span className={`stock-insignia ${valorEstado.clase} stock-insignia-inline`}>
                        {valorEstado.etiqueta}
                      </span>
                    </td>
                    <td className="tabla-acciones">
                      <button className="boton-enlace" onClick={() => setProductoQr(producto)}>
                        QR
                      </button>
                      <button className="boton-enlace" onClick={() => window.location.hash = '#salidas'}>
                        Salida
                      </button>
                      <button className="boton-enlace" onClick={() => setFormulario({ producto })}>
                        Editar
                      </button>
                      <button className="boton-enlace" onClick={() => cambiarEstado(producto)}>
                        {producto.activo ? 'Desactivar' : 'Reactivar'}
                      </button>
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
