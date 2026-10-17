import Usuarios from './Usuarios';
import './Admin.css';

function PanelAdmin({ token, usuario, onLogout }) {
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

      <main className="panel-contenido">
        <Usuarios token={token} usuarioActual={usuario} />
      </main>
    </div>
  );
}

export default PanelAdmin;
