"""Test GCP Pub/Sub publish + pull using project .env and ADC credentials.

    uv run python agent/api/pubsub/test_connection.py
"""

from __future__ import annotations

import os
import sys
import time
import uuid

from google.auth.exceptions import DefaultCredentialsError
from google.cloud import pubsub_v1

from agent.api._env import load_project_env


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required env var: {name}")
    return value


def main() -> int:
    load_project_env()

    project_id = _require_env("GCP_PROJECT_ID")
    topic_id = _require_env("GCP_TOPIC_ID")
    subscription_id = _require_env("GCP_SUBSCRIPTION_ID")

    topic_path = f"projects/{project_id}/topics/{topic_id}"
    subscription_path = f"projects/{project_id}/subscriptions/{subscription_id}"
    test_payload = f"governai-pubsub-python-{uuid.uuid4().hex[:12]}"

    try:
        publisher = pubsub_v1.PublisherClient()
        subscriber = pubsub_v1.SubscriberClient()
    except DefaultCredentialsError:
        print("Error: Application Default Credentials (ADC) not configured.")
        print("gcloud CLI auth alone is not enough for the Python client.")
        print("Run once:")
        print("  gcloud auth application-default login --project=jupiter-ai-498513")
        print("Or set GOOGLE_APPLICATION_CREDENTIALS to a service account JSON key.")
        return 1

    try:
        publisher.get_topic(request={"topic": topic_path})
        subscriber.get_subscription(request={"subscription": subscription_path})
    except Exception as exc:
        print(f"Error: cannot access topic/subscription: {exc}")
        return 1

    print("Pub/Sub resources OK")
    print(f"  project: {project_id}")
    print(f"  topic: {topic_id}")
    print(f"  subscription: {subscription_id}")

    future = publisher.publish(topic_path, test_payload.encode("utf-8"))
    message_id = future.result(timeout=30)
    print(f"Published message_id: {message_id}")

    deadline = time.time() + 30
    while time.time() < deadline:
        response = subscriber.pull(
            request={"subscription": subscription_path, "max_messages": 5},
            timeout=10,
        )
        for received in response.received_messages:
            data = received.message.data.decode("utf-8")
            if data == test_payload:
                subscriber.acknowledge(
                    request={
                        "subscription": subscription_path,
                        "ack_ids": [received.ack_id],
                    }
                )
                print("Pulled and acknowledged test message")
                print("Pub/Sub connection OK (publish + pull verified)")
                return 0

        time.sleep(1)

    print("Error: published message not received within 30s")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
