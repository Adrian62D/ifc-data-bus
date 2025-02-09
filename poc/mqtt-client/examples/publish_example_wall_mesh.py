"""Example demonstrating publishing IFC entities from a JSON file."""

import json
import hashlib
from time import sleep
from uuid import UUID
from pathlib import Path
from ifc_databus.core.bus import IfcBus

from compas_eve import set_default_transport
from compas_eve.mqtt import MqttTransport
from config import MQTT_HOST, MQTT_PORT


def global_id_to_uuid(global_id: str) -> UUID:
    """Convert an IFC globalId to a UUID.
    
    If the globalId is already a valid UUID, use it directly.
    Otherwise, create a UUID by hashing the globalId.
    """
    try:
        return UUID(global_id)
    except ValueError:
        # Hash the globalId to create a UUID
        md5 = hashlib.md5(global_id.encode())
        return UUID(md5.hexdigest())


def run_publish_mesh():
    """Run the mesh publishing example."""
    set_default_transport(MqttTransport(MQTT_HOST, MQTT_PORT))

    print("=== Starting Mesh Publisher ===")
    
    # Create bus instance
    bus = IfcBus("ifc_demo_1")
    
    # Connect to MQTT broker and wait for connection
    bus.connect()
    sleep(1)
    
    # Read JSON file
    json_path = Path(__file__).parent.parent.parent / "message" / "example_message_wall_mesh.json"
    with open(json_path) as f:
        data = json.load(f)
    
    # Publish each entity
    entities = {}
    for entity_data in data["data"]:
        entity_type = entity_data["type"]
        entity_id = global_id_to_uuid(entity_data["globalId"])
        
        # Keep all fields including type
        publish_data = entity_data.copy()
        
        # Publish entity
        print(f"\nPublishing {entity_type} with ID {entity_id}")
        entity_id = bus.publish_entity_with_id(entity_id, entity_type, publish_data)
        entities[entity_id] = entity_type
        sleep(1)  # Small delay between publishes
    
    print("\nPublished entities:")
    for entity_id, entity_type in entities.items():
        entity = bus._registers[entity_id]
        print(f"\n{entity_type} ({entity_id}):")
        print(f"Data: {entity.data}")
        print(f"Relationships: {entity.relationships}")
    
    # Keep running to receive updates
    try:
        print("\nListening for updates (Press Ctrl+C to stop)...")
        while True:
            sleep(1)
    except KeyboardInterrupt:
        print("\nStopping publisher...")
        bus.disconnect()


if __name__ == "__main__":
    run_publish_mesh()
