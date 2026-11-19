import { useEffect, useState } from 'react';
import { obtenerResumen } from '../../../services/api';

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

const ICONOS = {
  stock: (
    <Icono>
      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
      <line x1="12" y1="9" x2="12" y2="13" />
      <line x1="12" y1="17" x2="12.01" y2="17" />
    </Icono>
  ),
  alertas: (
    <Icono>
      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
      <path d="M13.73 21a2 2 0 0 1-3.46 0" />
    </Icono>
  ),
  cotizacion: (
    <Icono>
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
    </Icono>
  ),
  recibir: (
    <Icono>
      <rect x="1" y="3" width="15" height="13" />
      <polygon points="16 8 20 8 23 11 23 16 16 16 16 8" />
      <circle cx="5.5" cy="18.5" r="2.5" />
      <circle cx="18.5" cy="18.5" r="2.5" />
    </Icono>
  ),
  entrada: (
    <Icono>
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="7 10 12 15 17 10" />
      <line x1="12" y1="15" x2="12" y2="3" />
    </Icono>
  ),
  salida: (
    <Icono>
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="17 8 12 3 7 8" />
      <line x1="12" y1="3" x2="12" y2="15" />
    </Icono>
  ),
};

// Una tarjeta con un número que lleva a la sección donde se resuelve.
// "variante" solo cambia el color del ícono: rojo = urgente, amarillo = pendiente, azul = información.
function Tarjeta({ titulo, numero, texto, seccion, alerta, icono, variante }) {
  return (
    <a
      href={`#${seccion}`}
      className={`tarjeta-resumen tarjeta-enlace tarjeta-resumen-${variante} ${alerta && numero > 0 ? 'tarjeta-alerta' : ''}`}
    >
      <div className="tarjeta-resumen-header">
        <span className="tarjeta-resumen-icon">{ICONOS[icono]}</span>
        <span className="tarjeta-resumen-titulo">{titulo}</span>
      </div>
      <div className="tarjeta-resumen-body">
        <strong className="tarjeta-resumen-numero">{numero}</strong>
        <small className="tarjeta-resumen-subtitulo">{texto}</small>
      </div>
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
            <Tarjeta titulo="Stock bajo" numero={resumen.stock_bajo} texto="productos bajo el mínimo" seccion="productos" alerta icono="stock" variante="rojo" />
            <Tarjeta titulo="Alertas activas" numero={resumen.alertas_activas} texto="sin atender" seccion="alertas" alerta icono="alertas" variante="rojo" />
            <Tarjeta titulo="Por aprobar" numero={resumen.cotizaciones_por_aprobar} texto="cotizaciones registradas" seccion="cotizaciones" icono="cotizacion" variante="amarillo" />
            <Tarjeta titulo="Por recibir" numero={resumen.cotizaciones_por_recibir} texto="cotizaciones aprobadas" seccion="entradas" icono="recibir" variante="azul" />
            <Tarjeta titulo="Entradas hoy" numero={resumen.entradas_hoy} texto="movimientos de entrada" seccion="movimientos" icono="entrada" variante="verde" />
            <Tarjeta titulo="Salidas hoy" numero={resumen.salidas_hoy} texto="movimientos de salida" seccion="movimientos" icono="salida" variante="gris" />
          </div>

          <h3 className="seccion-subtitulo">Productos más críticos</h3>
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
                    <td className="sin-salto">
                      <span className="codigo-producto">{p.codigo}</span>
                    </td>
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