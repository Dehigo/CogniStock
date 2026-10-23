import { useEffect, useMemo, useState } from 'react';
import Agente from './agente/Agente';
import AlertasStock from './alertas/AlertasStock';
import Bitacora from './bitacora/Bitacora';
import Categorias from './categorias/Categorias';
import Cotizaciones from './cotizaciones/Cotizaciones';
import Entradas from './entradas/Entradas';
import Movimientos from './movimientos/Movimientos';
import Parametros from './parametros/Parametros';
import Productos from './productos/Productos';
import Proveedores from './proveedores/Proveedores';
import SalidasQR from './salidas/SalidasQR';
import { ROL_ADMINISTRADOR, SECCION_INICIAL, seccionesDelRol } from './secciones';
import Usuarios from './usuarios/Usuarios';
import '../../styles/admin.css';

const PANTALLAS = {
  usuarios: Usuarios,
  productos: Productos,
  categorias: Categorias,
  proveedores: Proveedores,
  cotizaciones: Cotizaciones,
  entradas: Entradas,
  movimientos: Movimientos,
  agente: Agente,
  salidas: SalidasQR,
  bitacora: Bitacora,
  alertas: AlertasStock,
  parametros: Parametros,
};

function seccionDesdeUrl(secciones) {
  const id = window.location.hash.slice(1);
  if (secciones.some((seccion) => seccion.id === id)) return id;
  return secciones.some((seccion) => seccion.id === SECCION_INICIAL) ? SECCION_INICIAL : secciones[0].id;
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
  const secciones = useMemo(() => seccionesDelRol(usuario.rol), [usuario.rol]);
  const grupos = [...new Set(secciones.map((seccion) => seccion.grupo))];
  const [seccionActiva, setSeccionActiva] = useState(() => seccionDesdeUrl(secciones));
  const [menuColapsado, setMenuColapsado] = useState(false);

  useEffect(() => {
    const alCambiarUrl = () => setSeccionActiva(seccionDesdeUrl(secciones));
    window.addEventListener('hashchange', alCambiarUrl);
    return () => window.removeEventListener('hashchange', alCambiarUrl);
  }, [secciones]);

  const seccion = secciones.find((s) => s.id === seccionActiva);
  const Pantalla = PANTALLAS[seccion.id];

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
            <span className="panel-subtitulo">
              {usuario.rol === ROL_ADMINISTRADOR ? 'Panel de administración' : 'Gestión de inventario'}
            </span>
          </div>
        </div>
        <div className="panel-sesion">
          <div className="panel-usuario">
            <span className="panel-usuario-avatar">{usuario.nombre?.charAt(0)?.toUpperCase() || 'U'}</span>
            <div className="panel-usuario-datos">
              <span className="panel-usuario-nombre">{usuario.nombre}</span>
              <span className="insignia insignia-base">{usuario.rol}</span>
            </div>
          </div>
          <button className="boton boton-secundario" onClick={onLogout}>
            Cerrar sesión
          </button>
        </div>
      </header>

      <div className="panel-cuerpo">
        <nav className={`menu ${menuColapsado ? 'menu-colapsado' : ''}`} aria-label="Secciones del panel">
          {grupos.map((grupo) => (
            <div key={grupo} className="menu-grupo">
              <span className="menu-grupo-titulo">{grupo}</span>
              {secciones.filter((s) => s.grupo === grupo).map((s) => (
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
