from django.core.management.base import BaseCommand
import paho.mqtt.client as mqtt
from django.utils import timezone
import json
import logging
from json.decoder import JSONDecodeError

from chat.models import Conversation, ChatIdentity
from main.models import Address
from chat.tasks import send_chat_notication


LOGGER = logging.getLogger(__name__)

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    LOGGER.info("Connected to MQTT broker with result code " + str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("chat/#")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload)
        if 'from' in payload.keys() and 'to' in payload.keys():
            LOGGER.info(f"Chat messsage received from {payload['from']} to {payload['to']}!")
            try:
                conversation_check = Conversation.objects.filter(topic=msg.topic)
                if conversation_check.exists():
                    conversation = conversation_check.last()
                    conversation.last_messaged = timezone.now()
                    conversation.save()
                    LOGGER.info('Conversation last messaged timestamp updated: ' + str(conversation.id))
                else:
                    conversation = Conversation(
                        from_address=Address.objects.get(address=payload['from']),
                        to_address=Address.objects.get(address=payload['to']),
                        topic=msg.topic,
                        last_messaged=timezone.now()
                    )
                    conversation.save()
                    LOGGER.info('Conversation saved: ' + str(conversation.id))

                try:
                    # Refresh the sender's `last_online` timestamp
                    sender_identity = ChatIdentity.objects.get(address__address=payload['from'])
                    sender_identity.last_online = timezone.now()
                    sender_identity.save()

                    # Send notification to recipient if not online for the last 5 minutes
                    recipient_identity = ChatIdentity.objects.get(address__address=payload['to'])
                    send_notif = False
                    if recipient_identity.last_online:
                        time_diff = timezone.now() - recipient_identity.last_online
                        if time_diff.total_seconds() < (60 * 5):
                            send_notif = True
                    else:
                        send_notif = True
                    if send_notif:
                        send_chat_notication.delay(payload['to'])
                except ChatIdentity.DoesNotExist:
                    pass

            except Address.DoesNotExist:
                pass
    except JSONDecodeError:
        pass

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect('docker-host', 1883, 60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
class Command(BaseCommand):
    help = 'Run the MQTT listener'

    def handle(self, *args, **options):
        client.loop_forever()
