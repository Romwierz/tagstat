"""Background MQTT collector: subscribes to the engine and fills a Store.

MQTT has no history, so a long-running subscriber must accumulate samples.
The collector runs paho's network loop on a background thread; the REPL (or
any caller) then queries the shared Store while data keeps flowing in.
"""
from __future__ import annotations
import paho.mqtt.client as mqtt
from .parse import parse_message
from .store import MemoryStore


class Collector:
    """Subscribes to `topic` and stores every parsed Sample in `store`."""

    def __init__(self, store=None, broker: str = "192.168.2.145",
                 port: int = 1883, topic: str = "engine/+/positions"):
        self.store = store if store is not None else MemoryStore()
        self.broker = broker
        self.port = port
        self.topic = topic
        self.received = 0      # messages stored OK
        self.errors = 0        # messages that failed to parse

        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        client.subscribe(self.topic)

    def _on_message(self, client, userdata, msg):
        try:
            self.store.add(parse_message(msg.payload))
            self.received += 1
        except ValueError:
            self.errors += 1   # malformed / position-less message — skip it

    def start(self) -> "Collector":
        """Connect and run the network loop on a background thread."""
        self._client.connect(self.broker, self.port, keepalive=60)
        self._client.loop_start()
        return self

    def stop(self) -> None:
        self._client.loop_stop()
        self._client.disconnect()
