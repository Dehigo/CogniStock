import { useEffect, useState } from 'react';
import { listarProductos } from '../../../services/api';

function AlertasStock({ token }) {
  const [productos, setProductos] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    listarProductos(token, { stock_bajo: 'true', activo: 'true' })
      .then(setProductos)
      .catch((err) => setError(err.message))
      .finally(() => setCargando(false));
  }, [token]);

  return (
    <section>
      <div className="seccion-cabecera">
        <h2>Alertas de stock</h2>
      </div>
      <p className="ayuda">Productos activos que tienen menos unidades que su stock mínimo.</p>

      {error && <p className="error">{error}</p>}

      <div className="tabla-contenedor">
        <table className="tabla">
          <thead>
            <tr>
              <th>Código</th>
              <th>Producto</th>
              <th>Categoría</th>
              <th>Stock actual</th>
              <th>Stock mínimo</th>
              <th>Faltan</th>
            </tr>
          </thead>
          <tbody>
            {cargando && (
              <tr>
                <td colSpan="6" className="tabla-mensaje">Revisando el stock...</td>
              </tr>
            )}

            {!cargando && productos.length === 0 && (
              <tr>
                <td colSpan="6" className="tabla-mensaje">Todo en orden: ningún producto está bajo su mínimo.</td>
              </tr>
            )}

            {!cargando &&
              productos.map((producto) => (
                <tr key={producto.id}>
                  <td className="sin-salto">{producto.codigo}</td>
                  <td>{producto.nombre}</td>
                  <td>{producto.categoria_nombre ?? 'Sin categoría'}</td>
                  <td className="sin-salto stock-bajo">{producto.stock_actual}</td>
                  <td className="sin-salto">{producto.stock_minimo}</td>
                  <td className="sin-salto">{producto.stock_minimo - producto.stock_actual}</td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export default AlertasStock;
