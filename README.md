# CampData – Monitorización de combustibles e IoT

Proyecto basado en Docker Compose que combina la consulta de precios de combustibles con un sistema de monitorización IoT mediante MQTT, Telegraf, InfluxDB y Grafana.

## Tecnologías utilizadas

- Docker y Docker Compose
- PostgreSQL
- Grafana
- Eclipse Mosquitto (MQTT)
- InfluxDB 2
- Telegraf
- Python

## Arquitectura

Los servicios se comunican mediante una red Docker compartida llamada `campdata`.

- **PostgreSQL:** almacena los datos de las estaciones y los precios.
- **Grafana:** permite visualizar los datos mediante dashboards.
- **Mosquitto:** recibe los mensajes MQTT.
- **Telegraf:** lee los mensajes MQTT y los envía a InfluxDB.
- **InfluxDB:** almacena los datos recibidos mediante MQTT.
- **Collector:** obtiene y procesa los precios de los combustibles.

## Instalación

### 1. Requisitos

- Docker
- Docker Compose

### 2. Configurar las variables de entorno

Copia el archivo de ejemplo:

```bash
cp .env.example .env
```

Edita el archivo `.env` y sustituye los valores de ejemplo por contraseñas y tokens propios.

Protege el archivo:

```bash
chmod 600 .env
```

### 3. Iniciar los contenedores

Desde la carpeta del proyecto:

```bash
docker compose up -d --build
```

### 4. Acceso a los servicios

- Grafana: http://localhost:3000
- Mosquitto MQTT: puerto 1883
- InfluxDB: puerto interno 8086

## Funcionamiento del sistema IoT

Los datos se publican en el tema MQTT:

```text
campdata/combustible
```

Telegraf se suscribe a los temas `campdata/#` y procesa los mensajes JSON. Posteriormente, envía los datos a InfluxDB, donde pueden consultarse desde Grafana.

## Publicar datos de combustibles por MQTT

Para volver a publicar los datos existentes sin insertar nuevos registros en PostgreSQL:

```bash
docker compose run --rm --entrypoint python collector /app/republicar_mqtt.py
```

Para ejecutar el proceso completo de recopilación:

```bash
docker compose run --rm collector
```

Este último proceso inserta datos en PostgreSQL, por lo que conviene evitar ejecuciones repetidas innecesarias.

## Actualizar los datos del Ministerio

El proyecto utiliza una copia local de los datos del Ministerio de Industria. Para actualizarla:

```bash
curl -sS -o collector/datos_api.json https://sedeaplicaciones.minetur.gob.es/ServiciosRESTCarburantes/PreciosCarburantes/EstacionesTerrestres/
```

Después, reconstruye la imagen:

```bash
docker compose build collector
```

## Detener los servicios

```bash
docker compose down
```

Los datos persistentes se conservan al detener los contenedores.

## Seguridad

El archivo `.env` contiene las contraseñas y tokens privados y no debe subirse al repositorio. Se proporciona `.env.example` como plantilla de configuración.
