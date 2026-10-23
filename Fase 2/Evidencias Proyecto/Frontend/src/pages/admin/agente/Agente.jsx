import { useCallback, useEffect, useState } from 'react';
import { consultarAgente, listarRecomendaciones, revisarRecomendacion } from '../../../services/api';
import { ROL_ADMINISTRADOR, ROL_ENCARGADO } from '../secciones';

const SUGERENCIAS = [
  '¿Qué productos tienen stock bajo?',
  '¿Cuáles fueron los últimos movimientos?',
  '¿Conviene reponer algún producto?',
];

function Agente({ token, usuarioActual }) {
  const puedeRevisar = [ROL_ADMINISTRADOR, ROL_ENCARGADO].includes(usuarioActual.rol);
  const [pregunta, setPregunta] = useState('');
  const [conversacion, setConversacion] = useState([]);
  const [recomendaciones, setRecomendaciones] = useState([]);
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState('');

  const cargarRecomendaciones = useCallback(() => {
    if (!puedeRevisar) return Promise.resolve();
    return listarRecomendaciones(token, { estado: 'PROPUESTA' })
      .then(setRecomendaciones)
      .catch((err) => setError(err.message));
  }, [token, puedeRevisar]);

  useEffect(() => {
    cargarRecomendaciones();
  }, [cargarRecomendaciones]);

  async function preguntar(texto) {
    const consulta = texto.trim();
    if (!consulta) return;

    setEnviando(true);
    setError('');
    try {
      const respuesta = await consultarAgente(token, consulta);
      setConversacion((actual) => [...actual, respuesta]);
      setPregunta('');
      if (respuesta.propuestas.length > 0) cargarRecomendaciones();
    } catch (err) {
      setError(err.message);
    } finally {
      setEnviando(false);
    }
  }

  async function revisar(recomendacion, estado) {
    try {
      await revisarRecomendacion(token, recomendacion.id, estado);
      cargarRecomendaciones();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <section>
      <div className="seccion-cabecera">
        <h2>Asistente IA</h2>
      </div>

      <p className="ayuda">
        El asistente consulta el inventario y puede proponer reposiciones. No registra entradas ni salidas ni cambia
        el stock: las propuestas quedan pendientes hasta que un encargado las revise.
      </p>

      <div className="agente-conversacion">
        {conversacion.length === 0 && (
          <div className="agente-sugerencias">
            {SUGERENCIAS.map((sugerencia) => (
              <button
                key={sugerencia}
                type="button"
                className="boton boton-chip"
                onClick={() => preguntar(sugerencia)}
                disabled={enviando}
              >
                {sugerencia}
              </button>
            ))}
          </div>
        )}

        {conversacion.map((mensaje) => (
          <div key={mensaje.id} className="agente-turno">
            <p className="agente-pregunta">{mensaje.pregunta}</p>
            <div className="agente-respuesta">
              <p>{mensaje.respuesta}</p>
              {mensaje.herramientas.length > 0 && (
                <small className="ayuda">
                  Consultó: {[...new Set(mensaje.herramientas.map((h) => h.tool))].join(', ')}
                </small>
              )}
            </div>
          </div>
        ))}

        {enviando && <p className="ayuda">El asistente está pensando...</p>}
      </div>

      {error && <p className="error">{error}</p>}

      <form
        className="filtros filtros-acciones"
        onSubmit={(e) => {
          e.preventDefault();
          preguntar(pregunta);
        }}
      >
        <input
          value={pregunta}
          onChange={(e) => setPregunta(e.target.value)}
          placeholder="Pregunta sobre el inventario"
          maxLength={500}
          aria-label="Pregunta"
        />
        <button type="submit" className="boton" disabled={enviando || !pregunta.trim()}>
          Preguntar
        </button>
      </form>

      {puedeRevisar && (
        <>
          <h3>Propuestas de reposición pendientes</h3>
          <div className="tabla-contenedor">
            <table className="tabla">
              <thead>
                <tr>
                  <th>Producto</th>
                  <th>Cantidad sugerida</th>
                  <th>Justificación</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {recomendaciones.length === 0 && (
                  <tr>
                    <td colSpan="4" className="tabla-mensaje">No hay propuestas pendientes.</td>
                  </tr>
                )}
                {recomendaciones.map((recomendacion) => (
                  <tr key={recomendacion.id}>
                    <td>
                      {recomendacion.producto_nombre} <span className="ayuda">{recomendacion.producto_codigo}</span>
                    </td>
                    <td className="sin-salto">{recomendacion.cantidad_sugerida}</td>
                    <td>{recomendacion.justificacion}</td>
                    <td className="tabla-acciones">
                      <button className="boton-enlace" onClick={() => revisar(recomendacion, 'ACEPTADA')}>
                        Aceptar
                      </button>
                      <button className="boton-enlace" onClick={() => revisar(recomendacion, 'DESCARTADA')}>
                        Descartar
                      </button>
                    </td>
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

export default Agente;
