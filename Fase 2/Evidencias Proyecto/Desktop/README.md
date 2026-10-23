# CogniStock — Escritorio (NW.js)

App de escritorio para **administradores** (D-12, RF-12). Abre el mismo panel web en una ventana propia
y solo habla con la API REST: la página no tiene acceso a Node, así que no puede tocar PostgreSQL (RN-04).
Si entra un usuario que no es Administrador, ve un aviso y no accede al panel.

## Cómo abrirla
1. Levanta el backend (`python manage.py runserver`) y el frontend (`npm run dev`).
2. En esta carpeta, la primera vez: `npm install` (descarga NW.js).
   Si npm avisa que bloqueó el script de `nw`, ejecuta `npm approve-scripts nw` y repite `npm install`.
3. Abrir la app: `npm start`

Para usarla con la web publicada, cambia `main` en `package.json` por esa dirección, manteniendo `?escritorio` al final.
