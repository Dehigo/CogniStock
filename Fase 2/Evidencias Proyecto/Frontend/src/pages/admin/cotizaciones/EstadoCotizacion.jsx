function EstadoCotizacion({ estado }) {
  return <span className={`estado estado-${estado.toLowerCase()}`}>{estado}</span>;
}

export default EstadoCotizacion;
