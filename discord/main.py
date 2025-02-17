import base64
import json
import functions_framework
import requests
from datetime import datetime

# Configura tu webhook URL de Discord
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1340742821463724186/qraP9mRJQ4rL2iVpnjN4ovBISk_rHV2x_9wCZNhmDL_-JiIbMd_y8SiuBM1XLxt2BWeK"

@functions_framework.cloud_event
def notify_discord(cloud_event):
    """
    Cloud Function que recibe eventos de Pub/Sub y envía notificaciones a Discord
    Args:
        cloud_event (CloudEvent): Evento de Pub/Sub codificado en base64
    """
    try:
        # Decodificar el mensaje de Pub/Sub
        pubsub_message = base64.b64decode(cloud_event.data["message"]["data"]).decode("utf-8")
        match_data = json.loads(pubsub_message)

        # Crear un mensaje formateado para Discord usando embeds
        discord_message = {
            "embeds": [{
                "title": "¡Nuevo Match Realizado! 🤝",
                "color": 3066993,  # Color verde
                "fields": [
                    {
                        "name": "Categoría",
                        "value": match_data["categoria"],
                        "inline": True
                    },
                    {
                        "name": "Distancia",
                        "value": f"{match_data['distance']:.2f} km",
                        "inline": True
                    },
                    {
                        "name": "Nivel de Urgencia",
                        "value": f"⚠️ {match_data['urgencia']}",
                        "inline": True
                    },
                    {
                        "name": "Persona que necesita ayuda",
                        "value": f"**Nombre:** {match_data['help_nombre']}\n**Población:** {match_data['help_poblacion']}",
                        "inline": False
                    },
                    {
                        "name": "Voluntario",
                        "value": f"**Nombre:** {match_data['volunteer_nombre']}\n**Población:** {match_data['volunteer_poblacion']}",
                        "inline": False
                    }
                ],
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {
                    "text": f"Match ID: {match_data['match_id']}"
                }
            }]
        }

        # Enviar la notificación a Discord
        response = requests.post(
            DISCORD_WEBHOOK_URL,
            json=discord_message
        )

        if response.status_code == 204:
            print(f"Notificación enviada exitosamente para match_id: {match_data['match_id']}")
            return {"status": "success"}
        else:
            raise Exception(f"Error al enviar notificación: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"Error procesando el mensaje: {str(e)}")
        raise e



