import { useState } from 'react';
import { crearParametro, editarParametro } from '../../../services/api';

function ParametroForm({ token, parametro, onGuardar, onCancelar }) {
  const esNuevo = parametro === null;
  const [clave, setClave] = useState(parametro?.clave ?? '');
  const [valor, setValor] = useState(parametro?.valor ?? '');
  const [descripcion, setDescripcion] = useState(parametro?.descripcion ?? '');
  const [error, setError] = useState('');
  const [guardando, setGuardando] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError('');
    setGuardando(true);

    const datos = { clave, valor, descripcion };

    try {
      if (esNuevo) {
        await crearParametro(token, datos);
      } else {
        await editarParametro(token, parametro.id, datos);
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
        <h3>{esNuevo ? 'Nuevo parámetro' : `Editar ${parametro.clave}`}</h3>

        <label htmlFor="clave">Clave</label>
        <input
          id="clave"
          value={clave}
          onChange={(e) => setClave(e.target.value)}
          placeholder="dias_cobertura"
          required
        />

        <label htmlFor="valor">Valor</label>
        <input id="valor" value={valor} onChange={(e) => setValor(e.target.value)} required />

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

export default ParametroForm;
