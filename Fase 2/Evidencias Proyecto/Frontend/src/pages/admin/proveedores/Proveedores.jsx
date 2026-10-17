import { useCallback, useEffect, useState } from 'react';
import { desactivarProveedor, editarProveedor, listarProveedores } from '../../../services/api';
import ProveedorForm from './ProveedorForm';

function Proveedores({ token }) {
  const [proveedores, setProveedores] = useState([]);
  const [buscar, setBuscar] = useState('');
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState('');
  const [formulario, setFormulario] = useState(null);

  const cargarProveedores = useCallback(async () => {
    try {
      setProveedores(await listarProveedores(token, { buscar }));
      setError('');
    } catch (err) {
      setError(err.message);
    } finally {
      setCargando(false);
    }
  }, [token, buscar]);

  useEffect(() => {
    const espera = setTimeout(cargarProveedores, 300);
    return () => clearTimeout(espera);
  }, [cargarProveedores]);

  async function cambiarEstado(proveedor) {
    const accion = proveedor.activo ? 'desactivar' : 'reactivar';
    if (!window.confirm(`¿Seguro que quieres ${accion} a ${proveedor.nombre}?`)) return;

    try {
      if (proveedor.activo) {
        await desactivarProveedor(token, proveedor.id);
      } else {
        await editarProveedor(token, proveedor.id, { activo: true });
      }
      cargarProveedores();
    } catch (err) {
      setError(err.message);
    }
  }

  function alGuardar() {
    setFormulario(null);
    cargarProveedores();
  }

  return (
    <section>
      <div className="seccion-cabecera">
        <h2>Proveedores</h2>
        <button className="boton" onClick={() => setFormulario({ proveedor: null })}>
          Nuevo proveedor
        </button>
      </div>

      <div className="filtros">
        <input
          type="search"
          placeholder="Buscar por nombre o RUT"
          value={buscar}
          onChange={(e) => setBuscar(e.target.value)}
        />
      </div>

      {error && <p className="error">{error}</p>}

      <div className="tabla-contenedor">
        <table className="tabla">
          <thead>
            <tr>
              <th>Nombre</th>
              <th>RUT</th>
              <th>Email</th>
              <th>Teléfono</th>
              <th>Estado</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {cargando && (
              <tr>
                <td colSpan="6" className="tabla-mensaje">Cargando proveedores...</td>
              </tr>
            )}

            {!cargando && proveedores.length === 0 && (
              <tr>
                <td colSpan="6" className="tabla-mensaje">No se encontraron proveedores.</td>
              </tr>
            )}

            {!cargando &&
              proveedores.map((proveedor) => (
                <tr key={proveedor.id}>
                  <td>{proveedor.nombre}</td>
                  <td className="sin-salto">{proveedor.rut}</td>
                  <td className="celda-email">{proveedor.email}</td>
                  <td className="sin-salto">{proveedor.telefono}</td>
                  <td className="sin-salto">
                    <span className={`estado ${proveedor.activo ? 'estado-activo' : 'estado-inactivo'}`}>
                      {proveedor.activo ? 'Activo' : 'Inactivo'}
                    </span>
                  </td>
                  <td className="tabla-acciones">
                    <button className="boton-enlace" onClick={() => setFormulario({ proveedor })}>
                      Editar
                    </button>
                    <button className="boton-enlace" onClick={() => cambiarEstado(proveedor)}>
                      {proveedor.activo ? 'Desactivar' : 'Reactivar'}
                    </button>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      {formulario && (
        <ProveedorForm
          token={token}
          proveedor={formulario.proveedor}
          onGuardar={alGuardar}
          onCancelar={() => setFormulario(null)}
        />
      )}
    </section>
  );
}

export default Proveedores;
