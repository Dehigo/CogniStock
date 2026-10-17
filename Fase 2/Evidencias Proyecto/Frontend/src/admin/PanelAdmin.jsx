import { useEffect, useState } from 'react';
import Categorias from './Categorias';
import Productos from './Productos';
import { SECCION_INICIAL, SECCIONES } from './secciones';
import Usuarios from './Usuarios';
import './Admin.css';

const GRUPOS = [...new Set(SECCIONES.map((seccion) => seccion.grupo))];

const PANTALLAS = {
  usuarios: Usuarios,
  productos: Productos,
  categorias: Categorias,
};

function seccionDesdeUrl() {
  const id = window.location.hash.slice(1);
  return SECCIONES.some((seccion) => seccion.id === id) ? id : SECCION_INICIAL;
}

function EnConstruccion({ seccion }) {
  return (
    <section>
      <div className="seccion-cabecera">
        <h2>{seccion.titulo}</h2>
      </div>
      <div className="en-construccion">
        <span className="en-construccion-etiqueta">En construcción · {seccion.requisito}</span>
        <p>{seccion.descripcion}</p>
      </div>
    </section>
  );
}

function PanelAdmin({ token, usuario, onLogout }) {
  const [seccionActiva, setSeccionActiva] = useState(seccionDesdeUrl);

  useEffect(() => {
    const alCambiarUrl = () => setSeccionActiva(seccionDesdeUrl());
    window.addEventListener('hashchange', alCambiarUrl);
    return () => window.removeEventListener('hashchange', alCambiarUrl);
  }, []);

  const seccion = SECCIONES.find((s) => s.id === seccionActiva);
  const Pantalla = PANTALLAS[seccion.id];

  return (
    <div className="panel">
      <header className="panel-cabecera">
        <div>
          <h1>CogniStock</h1>
          <span className="panel-subtitulo">Panel de administración</span>
        </div>
        <div className="panel-sesion">
          <span>{usuario.nombre}</span>
          <button className="boton boton-secundario" onClick={onLogout}>
            Cerrar sesión
          </button>
        </div>
      </header>

      <div className="panel-cuerpo">
        <nav className="menu" aria-label="Secciones del panel">
          {GRUPOS.map((grupo) => (
            <div key={grupo} className="menu-grupo">
              <span className="menu-grupo-titulo">{grupo}</span>
              {SECCIONES.filter((s) => s.grupo === grupo).map((s) => (
                <a
                  key={s.id}
                  href={`#${s.id}`}
                  className={`menu-enlace ${s.id === seccionActiva ? 'menu-enlace-activo' : ''}`}
                  aria-current={s.id === seccionActiva ? 'page' : undefined}
                >
                  {s.titulo}
                </a>
              ))}
            </div>
          ))}
        </nav>

        <main className="panel-contenido">
          {Pantalla ? (
            <Pantalla token={token} usuarioActual={usuario} />
          ) : (
            <EnConstruccion seccion={seccion} />
          )}
        </main>
      </div>
    </div>
  );
}

export default PanelAdmin;
