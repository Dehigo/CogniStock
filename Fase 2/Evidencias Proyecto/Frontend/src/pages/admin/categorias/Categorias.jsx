import { useEffect, useState } from 'react';
import { desactivarCategoria, editarCategoria, listarCategorias } from '../../../services/api';
import CategoriaForm from './CategoriaForm';

function Categorias({ token }) {
  const [categorias, setCategorias] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState('');
  const [formulario, setFormulario] = useState(null);

  const categoriasActivas = categorias.filter((categoria) => categoria.activo).length;
  const categoriasInactivas = categorias.length - categoriasActivas;

  useEffect(() => {
    listarCategorias(token)
      .then(setCategorias)
      .catch((err) => setError(err.message))
      .finally(() => setCargando(false));
  }, [token]);

  async function cargarCategorias() {
    try {
      setCategorias(await listarCategorias(token));
      setError('');
    } catch (err) {
      setError(err.message);
    }
  }

  async function cambiarEstado(categoria) {
    const accion = categoria.activo ? 'desactivar' : 'reactivar';
    if (!window.confirm(`¿Seguro que quieres ${accion} la categoría ${categoria.nombre}?`)) return;

    try {
      if (categoria.activo) {
        await desactivarCategoria(token, categoria.id);
      } else {
        await editarCategoria(token, categoria.id, { activo: true });
      }
      cargarCategorias();
    } catch (err) {
      setError(err.message);
    }
  }

  function alGuardar() {
    setFormulario(null);
    cargarCategorias();
  }

  return (
    <section>
      <div className="seccion-cabecera">
        <h2>Categorías</h2>
        <button className="boton" onClick={() => setFormulario({ categoria: null })}>
          Nueva categoría
        </button>
      </div>

      <div className="resumen-grid">
        <div className="tarjeta-resumen">
          <span className="tarjeta-resumen-titulo">Total</span>
          <strong className="tarjeta-resumen-numero">{categorias.length}</strong>
          <small className="tarjeta-resumen-subtitulo">categorías creadas</small>
        </div>
        <div className="tarjeta-resumen tarjeta-resumen-azul">
          <span className="tarjeta-resumen-titulo">Activas</span>
          <strong className="tarjeta-resumen-numero">{categoriasActivas}</strong>
          <small className="tarjeta-resumen-subtitulo">disponibles para uso</small>
        </div>
        <div className="tarjeta-resumen tarjeta-resumen-gris">
          <span className="tarjeta-resumen-titulo">Inactivas</span>
          <strong className="tarjeta-resumen-numero">{categoriasInactivas}</strong>
          <small className="tarjeta-resumen-subtitulo">ocultas temporalmente</small>
        </div>
      </div>

      {error && <p className="error">{error}</p>}

      <div className="tabla-contenedor">
        <table className="tabla">
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Descripción</th>
              <th>Estado</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {cargando && (
              <tr>
                <td colSpan="4" className="tabla-mensaje">Cargando categorías...</td>
              </tr>
            )}

            {!cargando && categorias.length === 0 && (
              <tr>
                <td colSpan="4" className="tabla-mensaje">Todavía no hay categorías.</td>
              </tr>
            )}

            {!cargando &&
              categorias.map((categoria) => (
                <tr key={categoria.id}>
                  <td>{categoria.nombre}</td>
                  <td>{categoria.descripcion}</td>
                  <td className="sin-salto">
                    <span className={`estado ${categoria.activo ? 'estado-activo' : 'estado-inactivo'}`}>
                      {categoria.activo ? 'Activa' : 'Inactiva'}
                    </span>
                  </td>
                  <td className="tabla-acciones">
                    <button className="boton-enlace" onClick={() => setFormulario({ categoria })}>
                      Editar
                    </button>
                    <button className="boton-enlace" onClick={() => cambiarEstado(categoria)}>
                      {categoria.activo ? 'Desactivar' : 'Reactivar'}
                    </button>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      {formulario && (
        <CategoriaForm
          token={token}
          categoria={formulario.categoria}
          onGuardar={alGuardar}
          onCancelar={() => setFormulario(null)}
        />
      )}
    </section>
  );
}

export default Categorias;
