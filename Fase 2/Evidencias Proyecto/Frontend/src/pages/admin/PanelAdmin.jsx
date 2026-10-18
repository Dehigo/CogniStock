import { useEffect, useState } from 'react';
import AlertasStock from './alertas/AlertasStock';
import Bitacora from './bitacora/Bitacora';
import Categorias from './categorias/Categorias';
import Parametros from './parametros/Parametros';
import Productos from './productos/Productos';
import Proveedores from './proveedores/Proveedores';
import SalidasQR from './salidas/SalidasQR';
import { SECCION_INICIAL, SECCIONES } from './secciones';
import Usuarios from './usuarios/Usuarios';
import '../../styles/admin.css';

const GRUPOS = [...new Set(SECCIONES.map((seccion) => seccion.grupo))];

const PANTALLAS = {
  usuarios: Usuarios,
  productos: Productos,
  categorias: Categorias,
  proveedores: Proveedores,
  salidas: SalidasQR,
  bitacora: Bitacora,
  alertas: AlertasStock,
  parametros: Parametros,
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
  const [menuColapsado, setMenuColapsado] = useState(false);

  useEffect(() => {
    const alCambiarUrl = () => setSeccionActiva(seccionDesdeUrl());
    window.addEventListener('hashchange', alCambiarUrl);
    return () => window.removeEventListener('hashchange', alCambiarUrl);
  }, []);

  const seccion = SECCIONES.find((s) => s.id === seccionActiva);
  const Pantalla = PANTALLAS[seccion.id];
  const rol = usuario?.rol ?? 'Usuario';

  return (
    <div className="panel">
      <header className="panel-cabecera">
        <div className="panel-cabecera-izq">
          <button
            type="button"
            className="boton-menu-toggle"
            onClick={() => setMenuColapsado((actual) => !actual)}
            aria-label={menuColapsado ? 'Expandir menú' : 'Colapsar menú'}
          >
            {menuColapsado ? '→' : '←'}
          </button>
          <div>
            <h1>CogniStock</h1>
            <span className="panel-subtitulo">Panel de administración</span>
          </div>
        </div>
        <div className="panel-sesion">
          <div className="panel-usuario">
            <span className="panel-usuario-avatar">{usuario.nombre?.charAt(0)?.toUpperCase() || 'U'}</span>
            <div className="panel-usuario-datos">
              <span className="panel-usuario-nombre">{usuario.nombre}</span>
              <span className="insignia insignia-base">{rol}</span>
            </div>
          </div>
          <button className="boton boton-secundario" onClick={onLogout}>
            Cerrar sesión
          </button>
        </div>
      </header>

      <div className="panel-cuerpo">
        <nav className={`menu ${menuColapsado ? 'menu-colapsado' : ''}`} aria-label="Secciones del panel">
          {GRUPOS.map((grupo) => (
            <div key={grupo} className="menu-grupo">
              <span className="menu-grupo-titulo">{grupo}</span>
              {SECCIONES.filter((s) => s.grupo === grupo).map((s) => (
                <a
                  key={s.id}
                  href={`#${s.id}`}
                  className={`menu-enlace ${s.id === seccionActiva ? 'menu-enlace-activo' : ''}`}
                  aria-current={s.id === seccionActiva ? 'page' : undefined}
                  title={s.titulo}
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
