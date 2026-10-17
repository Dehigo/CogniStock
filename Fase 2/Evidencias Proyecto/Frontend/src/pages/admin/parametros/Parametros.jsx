import { useEffect, useState } from 'react';
import { eliminarParametro, listarParametros } from '../../../services/api';
import ParametroForm from './ParametroForm';

function Parametros({ token }) {
  const [parametros, setParametros] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState('');
  const [formulario, setFormulario] = useState(null);

  useEffect(() => {
    listarParametros(token)
      .then(setParametros)
      .catch((err) => setError(err.message))
      .finally(() => setCargando(false));
  }, [token]);

  async function recargar() {
    try {
      setParametros(await listarParametros(token));
      setError('');
    } catch (err) {
      setError(err.message);
    }
  }

  async function eliminar(parametro) {
    if (!window.confirm(`¿Seguro que quieres eliminar el parámetro ${parametro.clave}?`)) return;

    try {
      await eliminarParametro(token, parametro.id);
      recargar();
    } catch (err) {
      setError(err.message);
    }
  }

  function alGuardar() {
    setFormulario(null);
    recargar();
  }

  return (
    <section>
      <div className="seccion-cabecera">
        <h2>Parámetros</h2>
        <button className="boton" onClick={() => setFormulario({ parametro: null })}>
          Nuevo parámetro
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      <div className="tabla-contenedor">
        <table className="tabla">
          <thead>
            <tr>
              <th>Clave</th>
              <th>Valor</th>
              <th>Descripción</th>
              <th>Modificado por</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {cargando && (
              <tr>
                <td colSpan="5" className="tabla-mensaje">Cargando parámetros...</td>
              </tr>
            )}

            {!cargando && parametros.length === 0 && (
              <tr>
                <td colSpan="5" className="tabla-mensaje">Todavía no hay parámetros.</td>
              </tr>
            )}

            {!cargando &&
              parametros.map((parametro) => (
                <tr key={parametro.id}>
                  <td className="sin-salto">{parametro.clave}</td>
                  <td>{parametro.valor}</td>
                  <td>{parametro.descripcion}</td>
                  <td>{parametro.actualizado_por_nombre ?? '—'}</td>
                  <td className="tabla-acciones">
                    <button className="boton-enlace" onClick={() => setFormulario({ parametro })}>
                      Editar
                    </button>
                    <button className="boton-enlace" onClick={() => eliminar(parametro)}>
                      Eliminar
                    </button>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      {formulario && (
        <ParametroForm
          token={token}
          parametro={formulario.parametro}
          onGuardar={alGuardar}
          onCancelar={() => setFormulario(null)}
        />
      )}
    </section>
  );
}

export default Parametros;
