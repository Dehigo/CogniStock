import { useEffect, useMemo, useRef, useState } from 'react';
import Agente from './agente/Agente';
import AlertasStock from './alertas/AlertasStock';
import Bitacora from './bitacora/Bitacora';
import Categorias from './categorias/Categorias';
import Cotizaciones from './cotizaciones/Cotizaciones';
import Entradas from './entradas/Entradas';
import Inicio from './inicio/Inicio';
import Movimientos from './movimientos/Movimientos';
import Parametros from './parametros/Parametros';
import Productos from './productos/Productos';
import Proveedores from './proveedores/Proveedores';
import SalidasQR from './salidas/SalidasQR';
import { ROL_ADMINISTRADOR, seccionesDelRol, seccionInicial } from './secciones';
import Usuarios from './usuarios/Usuarios';
import '../../styles/admin.css';

const PANTALLAS = {
  inicio: Inicio,
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

// Íconos del menú: uno por cada id de sección. Si agregas una sección nueva, súmale su ícono aquí.
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
  inicio: (
    <Icono>
      <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
      <polyline points="9 22 9 12 15 12 15 22" />
    </Icono>
  ),
  usuarios: (
    <Icono>
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </Icono>
  ),
  productos: (
    <Icono>
      <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
      <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
      <line x1="12" y1="22.08" x2="12" y2="12" />
    </Icono>
  ),
  categorias: (
    <Icono>
      <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z" />
      <line x1="7" y1="7" x2="7.01" y2="7" />
    </Icono>
  ),
  proveedores: (
    <Icono>
      <rect x="1" y="3" width="15" height="13" />
      <polygon points="16 8 20 8 23 11 23 16 16 16 16 8" />
      <circle cx="5.5" cy="18.5" r="2.5" />
      <circle cx="18.5" cy="18.5" r="2.5" />
    </Icono>
  ),
  cotizaciones: (
    <Icono>
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
    </Icono>
  ),
  entradas: (
    <Icono>
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="7 10 12 15 17 10" />
      <line x1="12" y1="15" x2="12" y2="3" />
    </Icono>
  ),
  salidas: (
    <Icono>
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="17 8 12 3 7 8" />
      <line x1="12" y1="3" x2="12" y2="15" />
    </Icono>
  ),
  movimientos: (
    <Icono>
      <polyline points="17 1 21 5 17 9" />
      <path d="M3 11V9a4 4 0 0 1 4-4h14" />
      <polyline points="7 23 3 19 7 15" />
      <path d="M21 13v2a4 4 0 0 1-4 4H3" />
    </Icono>
  ),
  alertas: (
    <Icono>
      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
      <path d="M13.73 21a2 2 0 0 1-3.46 0" />
    </Icono>
  ),
  agente: (
    <Icono>
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </Icono>
  ),
  bitacora: (
    <Icono>
      <circle cx="12" cy="12" r="10" />
      <polyline points="12 6 12 12 16 14" />
    </Icono>
  ),
  parametros: (
    <Icono>
      <line x1="4" y1="21" x2="4" y2="14" />
      <line x1="4" y1="10" x2="4" y2="3" />
      <line x1="12" y1="21" x2="12" y2="12" />
      <line x1="12" y1="8" x2="12" y2="3" />
      <line x1="20" y1="21" x2="20" y2="16" />
      <line x1="20" y1="12" x2="20" y2="3" />
      <line x1="1" y1="14" x2="7" y2="14" />
      <line x1="9" y1="8" x2="15" y2="8" />
      <line x1="17" y1="16" x2="23" y2="16" />
    </Icono>
  ),
};

const ICONO_MENU = (
  <Icono>
    <line x1="3" y1="12" x2="21" y2="12" />
    <line x1="3" y1="6" x2="21" y2="6" />
    <line x1="3" y1="18" x2="21" y2="18" />
  </Icono>
);

// En tablet y celular (hasta 1024 px) el menú se esconde y se abre con el botón de menú.
const PANTALLA_CHICA = '(max-width: 1024px)';
const esPantallaChica = () => window.matchMedia(PANTALLA_CHICA).matches;

// En celular las tablas se muestran como tarjetas. Para que cada dato diga qué es,
// se copia el título de su columna en la celda (data-label), y el CSS lo muestra.
function etiquetarTablas(contenedor) {
  contenedor.querySelectorAll('table.tabla').forEach((tabla) => {
    const titulos = [...tabla.querySelectorAll('thead th')].map((th) => th.textContent);
    tabla.querySelectorAll('tbody tr').forEach((fila) => {
      [...fila.children].forEach((celda, i) => {
        if (titulos[i] && celda.dataset.label !== titulos[i]) celda.dataset.label = titulos[i];
      });
    });
  });
}

function seccionDesdeUrl(secciones, rol) {
  const hash = window.location.hash.slice(1);
  const id = hash.split('?')[0] || '';
  return secciones.some((seccion) => seccion.id === id) ? id : seccionInicial(rol);
}

function PanelAdmin({ token, usuario, onLogout }) {
  const secciones = useMemo(() => seccionesDelRol(usuario.rol), [usuario.rol]);
  const grupos = [...new Set(secciones.map((seccion) => seccion.grupo))];
  const [seccionActiva, setSeccionActiva] = useState(() => seccionDesdeUrl(secciones, usuario.rol));
  const [menuAbierto, setMenuAbierto] = useState(() => !esPantallaChica());
  const contenido = useRef(null);

  useEffect(() => {
    const alCambiarUrl = () => setSeccionActiva(seccionDesdeUrl(secciones, usuario.rol));
    window.addEventListener('hashchange', alCambiarUrl);
    return () => window.removeEventListener('hashchange', alCambiarUrl);
  }, [secciones, usuario.rol]);

  // Las pantallas cargan sus tablas después de mostrarse, así que se re-etiquetan cada vez que cambian.
  useEffect(() => {
    const observador = new MutationObserver(() => etiquetarTablas(contenido.current));
    observador.observe(contenido.current, { childList: true, subtree: true });
    etiquetarTablas(contenido.current);
    return () => observador.disconnect();
  }, []);

  function elegirSeccion() {
    if (esPantallaChica()) setMenuAbierto(false);
  }

  const seccion = secciones.find((s) => s.id === seccionActiva);
  const Pantalla = PANTALLAS[seccion.id];

  return (
    <div className="panel panel-rol panel-rol-compartido">
      <header className="panel-cabecera">
        <div className="panel-cabecera-izq">
          <button
            type="button"
            className="boton-menu-toggle"
            onClick={() => setMenuAbierto((actual) => !actual)}
            aria-label={menuAbierto ? 'Cerrar menú' : 'Abrir menú'}
            aria-expanded={menuAbierto}
          >
            {ICONO_MENU}
          </button>
          <span className="panel-logo">{ICONOS.productos}</span>
          <div className="panel-titulos">
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
            Salir
          </button>
        </div>
      </header>

      <div className="panel-cuerpo">
        {/* En tablet y celular, tocar fuera del menú abierto lo cierra. */}
        {menuAbierto && <div className="menu-fondo" onClick={() => setMenuAbierto(false)} />}
        <nav className={`menu ${menuAbierto ? 'menu-abierto' : ''}`} aria-label="Secciones del panel">
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
                  onClick={elegirSeccion}
                >
                  <span className="menu-icon">{ICONOS[s.id]}</span>
                  {s.titulo}
                </a>
              ))}
            </div>
          ))}
        </nav>

        <main className="panel-contenido" ref={contenido}>
          <Pantalla token={token} usuarioActual={usuario} />
        </main>
      </div>
    </div>
  );
}

export default PanelAdmin;