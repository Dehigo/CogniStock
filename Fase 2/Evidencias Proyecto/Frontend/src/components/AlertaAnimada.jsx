import { useEffect, useRef, useState } from 'react';

let publicarAlerta;

export function mostrarAlerta(mensaje, tipo = 'error') {
  if (publicarAlerta) publicarAlerta({ mensaje, tipo, clave: Date.now() });
}

export default function AlertaAnimada() {
  const [alerta, setAlerta] = useState(null);
  const temporizador = useRef(null);

  useEffect(() => {
    publicarAlerta = (nuevaAlerta) => {
      setAlerta(nuevaAlerta);
      window.clearTimeout(temporizador.current);
      temporizador.current = window.setTimeout(() => setAlerta(null), 5200);
    };

    return () => {
      publicarAlerta = null;
      window.clearTimeout(temporizador.current);
    };
  }, []);

  if (!alerta) return null;

  return (
    <div className={`alerta-animada alerta-${alerta.tipo}`} role="alert" aria-live="assertive" key={alerta.clave}>
      <span className="alerta-animada-icono" aria-hidden="true">
        {alerta.tipo === 'success' ? '✓' : '!'}
      </span>
      <div className="alerta-animada-contenido">
        <strong>{alerta.tipo === 'success' ? 'Operación completada' : 'Revisa este dato'}</strong>
        <span>{alerta.mensaje}</span>
      </div>
      <button type="button" onClick={() => setAlerta(null)} aria-label="Cerrar mensaje">×</button>
    </div>
  );
}
