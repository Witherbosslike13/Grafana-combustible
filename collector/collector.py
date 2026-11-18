import os
import json
import requests
import psycopg2
import paho.mqtt.client as mqtt

from datetime import datetime

API_URL = (
    "https://sedeaplicaciones.minetur.gob.es/"
    "ServiciosRESTCarburantes/PreciosCarburantes/"
    "EstacionesTerrestres/"
)

MUNICIPIOS = [
    "Benaguasil",
    "Benisanó",
    "Bétera",
    "Casinos",
    "Eliana (l')",
    "Llíria",
    "Loriguilla",
    "Marines",
    "Náquera",
    "Olocau",
    "Pobla de Vallbona (la)",
    "Riba-roja de Túria",
    "San Antonio de Benagéber",
    "Serra",
    "Vilamarxant",
]

COMBUSTIBLES = {
    "Precio Gasolina 95 E5": "Gasolina 95",
    "Precio Gasolina 98 E5": "Gasolina 98",
    "Precio Gasoleo A": "Diésel A",
}


def conectar():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "campdata-postgres"),
        database="campdata",
        user="campdata",
        password=os.environ["DB_PASSWORD"],
        port=5432
    )


def obtener_datos():
    print("Leyendo datos del Ministerio desde el archivo local...")
    with open("/app/datos_api.json", "r", encoding="utf-8") as archivo:
        datos = json.load(archivo)
    return datos["ListaEESSPrecio"]

def main():
    estaciones = obtener_datos()

    municipios = {m.casefold() for m in MUNICIPIOS}

    filtradas = [
        e for e in estaciones
        if e["Provincia"].strip() == "VALENCIA / VALÈNCIA"
        and e["Municipio"].strip().casefold() in municipios
    ]

    print(f"Gasolineras encontradas: {len(filtradas)}")

    conexion = conectar()
    cursor = conexion.cursor()

    fecha = datetime.now()
    mensajes_mqtt = []

    for estacion in filtradas:
        municipio = estacion["Municipio"].strip()

        cursor.execute("""
            INSERT INTO municipalities (name)
            VALUES (%s)
            ON CONFLICT (name) DO NOTHING
        """, (municipio,))

        cursor.execute(
            "SELECT id FROM municipalities WHERE name = %s",
            (municipio,)
        )
        municipio_id = cursor.fetchone()[0]

        codigo = estacion["IDEESS"]

        cursor.execute("""
            INSERT INTO gas_stations
            (station_code, name, brand, address,
             municipality_id, latitude, longitude, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (station_code) DO UPDATE SET
                name = EXCLUDED.name,
                brand = EXCLUDED.brand,
                address = EXCLUDED.address,
                municipality_id = EXCLUDED.municipality_id,
                latitude = EXCLUDED.latitude,
                longitude = EXCLUDED.longitude,
                updated_at = EXCLUDED.updated_at
            RETURNING id
        """, (
            codigo,
            estacion.get("Rótulo"),
            estacion.get("Rótulo"),
            estacion.get("Dirección"),
            municipio_id,
            float(estacion["Latitud"].replace(",", ".")),
            float(estacion["Longitud (WGS84)"].replace(",", ".")),
            fecha
        ))

        station_id = cursor.fetchone()[0]

        for campo, nombre in COMBUSTIBLES.items():
            valor = estacion.get(campo, "").strip()

            if not valor:
                continue

            precio = float(valor.replace(",", "."))

            cursor.execute("""
                INSERT INTO fuel_prices
                (station_id, fuel_type, price, recorded_at)
                VALUES (%s, %s, %s, %s)
            """, (station_id, nombre, precio, fecha))

            mensaje = {
                "gasolinera": estacion.get("Rótulo"),
                "municipio": municipio,
                "combustible": nombre,
                "precio": precio,
                "fecha": fecha.isoformat()
            }

            mensajes_mqtt.append(mensaje)

    conexion.commit()
    cursor.close()
    conexion.close()

    print(f"Actualización completada: {len(filtradas)} gasolineras")
    print("Datos guardados en PostgreSQL.")

    print("Conectando con Mosquitto...")

    cliente = mqtt.Client()
    cliente.connect(
        os.getenv("MQTT_HOST", "mosquitto"),
        int(os.getenv("MQTT_PORT", "1883")),
        60
    )

    cliente.loop_start()

    for mensaje in mensajes_mqtt:
        resultado = cliente.publish(
            "campdata/combustible",
            json.dumps(mensaje, ensure_ascii=False),
            qos=1
        )
        resultado.wait_for_publish()

    cliente.loop_stop()
    cliente.disconnect()

    print(f"Mensajes enviados a MQTT: {len(mensajes_mqtt)}")
    print("Tópico: campdata/combustible")


if __name__ == "__main__":
    main()
