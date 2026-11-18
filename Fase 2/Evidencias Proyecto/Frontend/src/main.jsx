import { createRoot } from 'react-dom/client'
import './styles/index.css'
import App from './App.jsx'
import AlertaAnimada, { mostrarAlerta } from './components/AlertaAnimada.jsx'

window.addEventListener('invalid', (evento) => {
  const campo = evento.target;
  if (!(campo instanceof HTMLInputElement || campo instanceof HTMLSelectElement || campo instanceof HTMLTextAreaElement)) return;

  evento.preventDefault();
  campo.focus();
  const etiqueta = campo.labels?.[0]?.textContent?.trim();
  let mensaje = campo.validationMessage;

  if (campo.validity.valueMissing) {
    mensaje = etiqueta ? `Completa el campo ${etiqueta}.` : 'Completa este campo.';
  } else if (campo.validity.typeMismatch) {
    mensaje = etiqueta ? `Ingresa un dato válido en ${etiqueta}.` : 'Ingresa un dato válido.';
  }

  mostrarAlerta(mensaje);
}, true);

createRoot(document.getElementById('root')).render(
  <>
    <App />
    <AlertaAnimada />
  </>
)