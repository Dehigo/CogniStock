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

// En tablet y celular (hasta 1024 px) el menú se esconde y se abre con el botón ☰.
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
  const id = window.location.hash.slice(1);
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
    <div className="panel">
      <header className="panel-cabecera">
        <div className="panel-cabecera-izq">
          <button
            type="button"
            className="boton-menu-toggle"
            onClick={() => setMenuAbierto((actual) => !actual)}
            aria-label={menuAbierto ? 'Cerrar menú' : 'Abrir menú'}
            aria-expanded={menuAbierto}
          >
            ☰
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
