"""
In-process notification store.

In production, replace this list with a Redis stream, a database table,
or a proper message queue (Kafka, RabbitMQ, etc.).
"""
from typing import List

SENT_NOTIFICATIONS: List[str] = []
