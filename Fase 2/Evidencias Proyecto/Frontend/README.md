# Frontend - CogniStock

Este documento explica cómo instalar dependencias y levantar la aplicación frontend del proyecto CogniStock.

## Requisitos previos

Asegúrate de tener instalado:

- Node.js 18 o superior
- npm (incluido con Node.js)
- Git

Puedes verificar la versión con:

```bash
node -v
npm -v
```

## 1. Entrar al directorio del frontend

```bash
cd "Fase 2/Evidencias Proyecto/Frontend"
```

Si estás en Ubuntu/WSL y la ruta está en tu home, también puede ser:

```bash
cd ~/CogniStock/Fase\ 2/Evidencias\ Proyecto/Frontend
```

## 2. Instalar dependencias

```bash
npm install
```

Esto descargará todas las librerías necesarias para ejecutar la interfaz.

## 3. Levantar la aplicación

Para iniciar el servidor de desarrollo:

```bash
npm run dev
```

Por defecto, Vite normalmente quedará disponible en:

```text
http://localhost:5173
```

Si deseas que quede accesible desde otras máquinas o contenedores, puedes usar:

```bash
npm run dev -- --host 0.0.0.0
```

## 4. Construir la versión de producción

```bash
npm run build
```

Esto genera la carpeta `dist` con la versión lista para despliegue.

## 5. Previsualizar la versión compilada

```bash
npm run preview -- --host 0.0.0.0
```

## 6. Verificar código (opcional)

```bash
npm run lint
```

## Solución de problemas comunes

### Error de Node no encontrado
Instala Node.js 18+ y vuelve a ejecutar los comandos.

### Puerto 5173 ocupado
Cambia el puerto manualmente:

```bash
npm run dev -- --port 4173
```

### Dependencias no instaladas correctamente
Elimina la carpeta `node_modules` y reinstala:

```bash
rm -rf node_modules
npm install
```

## Estructura principal

```text
Frontend/
├── package.json
├── vite.config.js
├── index.html
├── public/
├── src/
└── README.md
```

Si necesitas ayuda con la integración del frontend con el backend, puedes consultar el README del proyecto principal o el archivo de configuración del backend.
