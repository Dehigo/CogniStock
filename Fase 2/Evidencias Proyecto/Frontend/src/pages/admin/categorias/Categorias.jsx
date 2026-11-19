import { useEffect, useState } from 'react';
import { desactivarCategoria, editarCategoria, listarCategorias } from '../../../services/api';
import CategoriaForm from './CategoriaForm';

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

const ICONO_TOTAL = (
  <Icono>
    <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z" />
    <line x1="7" y1="7" x2="7.01" y2="7" />
  </Icono>
);

const ICONO_ACTIVAS = (
  <Icono>
    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
    <polyline points="22 4 12 14.01 9 11.01" />
  </Icono>
);

const ICONO_INACTIVAS = (
  <Icono>
    <circle cx="12" cy="12" r="10" />
    <line x1="8" y1="12" x2="16" y2="12" />
  </Icono>
);

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
        <div className="tarjeta-resumen tarjeta-resumen-azul">
          <div className="tarjeta-resumen-header">
            <span className="tarjeta-resumen-icon">{ICONO_TOTAL}</span>
            <span className="tarjeta-resumen-titulo">Total</span>
          </div>
          <div className="tarjeta-resumen-body">
            <strong className="tarjeta-resumen-numero">{categorias.length}</strong>
            <small className="tarjeta-resumen-subtitulo">categorías creadas</small>
          </div>
        </div>
        <div className="tarjeta-resumen tarjeta-resumen-verde">
          <div className="tarjeta-resumen-header">
            <span className="tarjeta-resumen-icon">{ICONO_ACTIVAS}</span>
            <span className="tarjeta-resumen-titulo">Activas</span>
          </div>
          <div className="tarjeta-resumen-body">
            <strong className="tarjeta-resumen-numero">{categoriasActivas}</strong>
            <small className="tarjeta-resumen-subtitulo">disponibles para uso</small>
          </div>
        </div>
        <div className="tarjeta-resumen tarjeta-resumen-gris">
          <div className="tarjeta-resumen-header">
            <span className="tarjeta-resumen-icon">{ICONO_INACTIVAS}</span>
            <span className="tarjeta-resumen-titulo">Inactivas</span>
          </div>
          <div className="tarjeta-resumen-body">
            <strong className="tarjeta-resumen-numero">{categoriasInactivas}</strong>
            <small className="tarjeta-resumen-subtitulo">ocultas temporalmente</small>
          </div>
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