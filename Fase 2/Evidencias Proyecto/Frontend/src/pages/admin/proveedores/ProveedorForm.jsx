import { useState } from 'react';
import { crearProveedor, editarProveedor } from '../../../services/api';

function ProveedorForm({ token, proveedor, onGuardar, onCancelar }) {
  const esNuevo = proveedor === null;
  const [nombre, setNombre] = useState(proveedor?.nombre ?? '');
  const [rut, setRut] = useState(proveedor?.rut ?? '');
  const [email, setEmail] = useState(proveedor?.email ?? '');
  const [telefono, setTelefono] = useState(proveedor?.telefono ?? '');
  const [error, setError] = useState('');
  const [guardando, setGuardando] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError('');
    setGuardando(true);

    const datos = { nombre, rut, email, telefono };

    try {
      if (esNuevo) {
        await crearProveedor(token, datos);
      } else {
        await editarProveedor(token, proveedor.id, datos);
      }
      onGuardar();
    } catch (err) {
      setError(err.message);
    } finally {
      setGuardando(false);
    }
  }

  return (
    <div className="modal-fondo" onClick={onCancelar}>
      <form className="modal" onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
        <h3>{esNuevo ? 'Nuevo proveedor' : `Editar ${proveedor.nombre}`}</h3>

        <label htmlFor="nombre">Nombre</label>
        <input id="nombre" value={nombre} onChange={(e) => setNombre(e.target.value)} required />

        <label htmlFor="rut">RUT</label>
        <input id="rut" value={rut} onChange={(e) => setRut(e.target.value)} placeholder="76.123.456-7" />

        <label htmlFor="email">Email</label>
        <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />

        <label htmlFor="telefono">Teléfono</label>
        <input id="telefono" value={telefono} onChange={(e) => setTelefono(e.target.value)} />

        {error && <p className="error">{error}</p>}

        <div className="modal-acciones">
          <button type="button" className="boton boton-secundario" onClick={onCancelar}>
            Cancelar
          </button>
          <button type="submit" className="boton" disabled={guardando}>
            {guardando ? 'Guardando...' : 'Guardar'}
          </button>
        </div>
      </form>
    </div>
  );
}

export default ProveedorForm;
