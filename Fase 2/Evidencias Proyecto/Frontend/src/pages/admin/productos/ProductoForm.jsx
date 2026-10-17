import { useState } from 'react';
import { crearProducto, editarProducto } from '../../../services/api';

function ProductoForm({ token, producto, categorias, onGuardar, onCancelar }) {
  const esNuevo = producto === null;
  const [codigo, setCodigo] = useState(producto?.codigo ?? '');
  const [codigoBarras, setCodigoBarras] = useState(producto?.codigo_qr ?? '');
  const [nombre, setNombre] = useState(producto?.nombre ?? '');
  const [descripcion, setDescripcion] = useState(producto?.descripcion ?? '');
  const [categoria, setCategoria] = useState(producto?.categoria ?? '');
  const [precio, setPrecio] = useState(producto?.precio_referencia ?? 0);
  const [stockMinimo, setStockMinimo] = useState(producto?.stock_minimo ?? 0);
  const [error, setError] = useState('');
  const [guardando, setGuardando] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError('');
    setGuardando(true);

    const datos = {
      codigo,
      codigo_qr: codigoBarras,
      nombre,
      descripcion,
      categoria: categoria === '' ? null : Number(categoria),
      precio_referencia: Number(precio),
      stock_minimo: Number(stockMinimo),
    };

    try {
      if (esNuevo) {
        await crearProducto(token, datos);
      } else {
        await editarProducto(token, producto.id, datos);
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
      <form className="modal modal-ancho" onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
        <h3>{esNuevo ? 'Nuevo producto' : `Editar ${producto.nombre}`}</h3>

        <div className="fila-doble">
          <div>
            <label htmlFor="codigo">Código interno</label>
            <input id="codigo" value={codigo} onChange={(e) => setCodigo(e.target.value)} required />
          </div>
          <div>
            <label htmlFor="categoria">Categoría</label>
            <select id="categoria" value={categoria} onChange={(e) => setCategoria(e.target.value)}>
              <option value="">Sin categoría</option>
              {categorias.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.activo ? c.nombre : `${c.nombre} (inactiva)`}
                </option>
              ))}
            </select>
          </div>
        </div>

        <label htmlFor="nombre">Nombre</label>
        <input id="nombre" value={nombre} onChange={(e) => setNombre(e.target.value)} required />

        <label htmlFor="descripcion">Descripción</label>
        <textarea id="descripcion" rows="2" value={descripcion} onChange={(e) => setDescripcion(e.target.value)} />

        <label htmlFor="codigo-barras">Código de barras</label>
        <input
          id="codigo-barras"
          value={codigoBarras}
          onChange={(e) => setCodigoBarras(e.target.value)}
          placeholder="El que viene impreso en el envase"
        />
        <p className="ayuda">Si el producto no trae uno, déjalo vacío y se generará un código para imprimir.</p>

        <div className="fila-doble">
          <div>
            <label htmlFor="precio">Precio de referencia</label>
            <input
              id="precio"
              type="number"
              min="0"
              step="1"
              value={precio}
              onChange={(e) => setPrecio(e.target.value)}
              required
            />
          </div>
          <div>
            <label htmlFor="stock-minimo">Stock mínimo (unidades)</label>
            <input
              id="stock-minimo"
              type="number"
              min="0"
              step="1"
              value={stockMinimo}
              onChange={(e) => setStockMinimo(e.target.value)}
              required
            />
          </div>
        </div>
        <p className="ayuda">
          El stock parte en 0 y aumenta al registrar entradas. Bajo el stock mínimo, el producto se marca en rojo.
        </p>

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

export default ProductoForm;
