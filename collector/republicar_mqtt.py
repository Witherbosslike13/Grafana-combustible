import os
import json
import paho.mqtt.client as mqtt
from collector import obtener_datos, MUNICIPIOS, COMBUSTIBLES

print("Leyendo datos del Ministerio...")

estaciones = obtener_datos()
municipios = {m.casefold() for m in MUNICIPIOS}

mensajes = []

for estacion in estaciones:
    if estacion["Provincia"].strip() != "VALENCIA / VALÈNCIA":
        continue

    municipio = estacion["Municipio"].strip()

    if municipio.casefold() not in municipios:
        continue

    for campo, nombre in COMBUSTIBLES.items():
        valor = estacion.get(campo, "").strip()

        if not valor:
            continue

        mensaje = {
            "gasolinera": estacion.get("Rótulo"),
            "municipio": municipio,
            "combustible": nombre,
            "precio": float(valor.replace(",", "."))
        }

        mensajes.append(mensaje)

print(f"Mensajes preparados: {len(mensajes)}")
print("Conectando con Mosquitto...")

cliente = mqtt.Client()
cliente.connect(
    os.getenv("MQTT_HOST", "mosquitto"),
    int(os.getenv("MQTT_PORT", "1883")),
    60
)

cliente.loop_start()

for mensaje in mensajes:
    resultado = cliente.publish(
        "campdata/combustible",
        json.dumps(mensaje, ensure_ascii=False),
        qos=1
    )
    resultado.wait_for_publish()

cliente.loop_stop()
cliente.disconnect()

print(f"Mensajes publicados: {len(mensajes)}")
