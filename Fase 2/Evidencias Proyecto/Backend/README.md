# Backend de CogniStock

Este es un proyecto de Django configurado con un entorno virtual basado en Python 3.10 via `pyenv` y una base de datos PostgreSQL ejecutándose en un contenedor Docker.

---

## Requisitos Previos

Asegúrate de tener instalados los siguientes componentes en tu sistema:

* [pyenv](https://github.com/pyenv/pyenv)
* [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv) (opcional, si prefieres gestionar entornos virtuales directamente con pyenv)
* [Docker](https://www.docker.com/) y [Docker Compose](https://docs.docker.com/compose/)
* [Git](https://git-scm.com/)

---

## Configuración del Entorno de Desarrollo

### 1. Clonar el Repositorio

```bash
git clone https://github.com/Dehigo/CogniStock/
cd CogniStock
```

### 2. Configurar Python 3.10 con pyenv
 Conversation with Gemini

Creame un reade.md para un proyecto de django con pyenv 3.10 venv postgre en docker
Markdown

# Django Project

Este es un proyecto de Django configurado con un entorno virtual basado en Python 3.10 via `pyenv` y una base de datos PostgreSQL ejecutándose en un contenedor Docker.

---

## Requisitos Previos

Asegúrate de tener instalados los siguientes componentes en tu sistema:

* [pyenv](https://github.com/pyenv/pyenv)
* [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv) (opcional, si prefieres gestionar entornos virtuales directamente con pyenv)
* [Docker](https://www.docker.com/) y [Docker Compose](https://docs.docker.com/compose/)
* [Git](https://git-scm.com/)

---

## Configuración del Entorno de Desarrollo

### 1. Clonar el Repositorio

```bash
git clone https://github.com/Dehigo/CogniStock/
cd CogniStock
```
### 2. Configurar Python 3.10 con pyenv

Instala Python 3.10 si aún no lo tienes instalado:

```bash
pyenv install 3.10
```

Crea y activa el entorno virtual para este proyecto:

```bash 
# Crear el entorno virtual
pyenv virtualenv 3.10 venv-django
 
# Establecer la versión local dentro del directorio del proyecto
pyenv local venv
```

### Crea tus Variables de Entorno

```
DEBUG=True
SECRET_KEY=
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=
```

### 3. Instalar dependencias de Python
```bash 
python -m pip install --upgrade pip
pip install -r requirements.txt
``` 
## PostgreSQL en Docker

### 1. Iniciar el Contenedor de PostgreSQL
```bash 
docker-compose up -d postgres
```

Para verificar que el servicio está corriendo correctamente:
```bash 
docker ps
```

## Ejecución del Proyecto Django

### 1. Aplicar Migraciones
Ejecuta las migraciones pendientes para preparar el esquema en la base de datos PostgreSQL:
```bash 
python manage.py migrate
```

### 2. Crear un Superusuario
Crea la cuenta de administrador para acceder al panel de Django:
```bash 
python manage.py createsuperuser
```

### 3. Iniciar el Servidor de Desarrollo
Crea la cuenta de administrador para acceder al panel de Django:
```bash 
python manage.py runserver
```
El proyecto estará disponible en http://127.0.0.1:8000/.

Comandos Útiles

    Crear nuevas migraciones: python manage.py makemigrations

    Ejecutar pruebas unitarias: python manage.py test

    Acceder a la consola interactiva de Django: python manage.py shell

    Acceder a la consola de PostgreSQL en Docker:
    
    docker-compose exec postgres psql -U nombre-d usuario

### Estructura del Proyecto

    ├── .env          # Variables de entorno
    ├── .gitignore            # Archivos excluidos en Git
    ├── docker-compose.yml    # Configuración de Docker para PostgreSQL
    ├── manage.py             # Script principal de gestión de Django
    ├── requirements.txt      # Dependencias de Python
    └── README.md             # Documentación del proyecto