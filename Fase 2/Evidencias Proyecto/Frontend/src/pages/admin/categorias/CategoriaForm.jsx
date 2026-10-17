import { useState } from 'react';
import { crearCategoria, editarCategoria } from '../../../services/api';

function CategoriaForm({ token, categoria, onGuardar, onCancelar }) {
  const esNueva = categoria === null;
  const [nombre, setNombre] = useState(categoria?.nombre ?? '');
  const [descripcion, setDescripcion] = useState(categoria?.descripcion ?? '');
  const [error, setError] = useState('');
  const [guardando, setGuardando] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError('');
    setGuardando(true);

    const datos = { nombre, descripcion };

    try {
      if (esNueva) {
        await crearCategoria(token, datos);
      } else {
        await editarCategoria(token, categoria.id, datos);
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
        <h3>{esNueva ? 'Nueva categoría' : `Editar ${categoria.nombre}`}</h3>

        <label htmlFor="nombre">Nombre</label>
        <input id="nombre" value={nombre} onChange={(e) => setNombre(e.target.value)} required />

        <label htmlFor="descripcion">Descripción</label>
        <input id="descripcion" value={descripcion} onChange={(e) => setDescripcion(e.target.value)} />

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

export default CategoriaForm;
