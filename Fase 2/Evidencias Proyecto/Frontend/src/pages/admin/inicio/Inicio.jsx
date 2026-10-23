import { useEffect, useState } from 'react';
import { obtenerResumen } from '../../../services/api';

// Una tarjeta con un número que lleva a la sección donde se resuelve.
function Tarjeta({ titulo, numero, texto, seccion, alerta }) {
  return (
    <a href={`#${seccion}`} className={`tarjeta-resumen tarjeta-enlace ${alerta && numero > 0 ? 'tarjeta-alerta' : ''}`}>
      <span className="tarjeta-resumen-titulo">{titulo}</span>
      <strong className="tarjeta-resumen-numero">{numero}</strong>
      <small className="tarjeta-resumen-subtitulo">{texto}</small>
    </a>
  );
}

// Pantalla de inicio del encargado: lo que necesita atención hoy.
function Inicio({ token, usuarioActual }) {
  const [resumen, setResumen] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    obtenerResumen(token)
      .then(setResumen)
      .catch((err) => setError(err.message));
  }, [token]);

  return (
    <section>
      <div className="seccion-cabecera">
        <h2>Hola, {usuarioActual.nombre}</h2>
      </div>

      {error && <p className="error">{error}</p>}
      {!resumen && !error && <p className="ayuda">Cargando resumen...</p>}

      {resumen && (
        <>
          <div className="resumen-grid">
            <Tarjeta titulo="Stock bajo" numero={resumen.stock_bajo} texto="productos bajo el mínimo" seccion="productos" alerta />
            <Tarjeta titulo="Alertas activas" numero={resumen.alertas_activas} texto="sin atender" seccion="alertas" alerta />
            <Tarjeta titulo="Por aprobar" numero={resumen.cotizaciones_por_aprobar} texto="cotizaciones registradas" seccion="cotizaciones" />
            <Tarjeta titulo="Por recibir" numero={resumen.cotizaciones_por_recibir} texto="cotizaciones aprobadas" seccion="entradas" />
            <Tarjeta titulo="Entradas hoy" numero={resumen.entradas_hoy} texto="movimientos de entrada" seccion="movimientos" />
            <Tarjeta titulo="Salidas hoy" numero={resumen.salidas_hoy} texto="movimientos de salida" seccion="movimientos" />
          </div>

          <h3>Productos más críticos</h3>
          <div className="tabla-contenedor">
            <table className="tabla">
              <thead>
                <tr>
                  <th>Código</th>
                  <th>Producto</th>
                  <th>Stock</th>
                  <th>Mínimo</th>
                </tr>
              </thead>
              <tbody>
                {resumen.productos_criticos.length === 0 && (
                  <tr>
                    <td colSpan="4" className="tabla-mensaje">Ningún producto está bajo el mínimo.</td>
                  </tr>
                )}
                {resumen.productos_criticos.map((p) => (
                  <tr key={p.codigo}>
                    <td className="sin-salto">{p.codigo}</td>
                    <td>{p.nombre}</td>
                    <td className="sin-salto">
                      <span className="stock-insignia stock-bajo">{p.stock}</span>
                    </td>
                    <td className="sin-salto">{p.minimo}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </section>
  );
}

export default Inicio;
