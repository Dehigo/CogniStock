import QRCode from 'qrcode';
import { useEffect, useState } from 'react';

function QrProducto({ producto, onCerrar }) {
  const [imagen, setImagen] = useState('');

  useEffect(() => {
    QRCode.toDataURL(producto.codigo_qr, { width: 260, margin: 2 }).then(setImagen);
  }, [producto.codigo_qr]);

  return (
    <div className="modal-fondo" onClick={onCerrar}>
      <div className="modal qr" onClick={(e) => e.stopPropagation()}>
        <h3>{producto.nombre}</h3>

        {imagen && <img className="qr-imagen" src={imagen} alt={`Código QR de ${producto.nombre}`} />}
        <span className="qr-codigo">{producto.codigo_qr}</span>

        <div className="modal-acciones">
          <button type="button" className="boton boton-secundario" onClick={onCerrar}>
            Cerrar
          </button>
          <a className="boton" href={imagen} download={`qr-${producto.codigo}.png`}>
            Descargar
          </a>
        </div>
      </div>
    </div>
  );
}

export default QrProducto;
