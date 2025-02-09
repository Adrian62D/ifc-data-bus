"""Example demonstrating publishing IFC entities from a JSON file with file monitoring."""

import json
import hashlib
import time
import base64
from uuid import UUID
from pathlib import Path
from ifc_databus.core.bus import IfcBus
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

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


class JsonFileHandler(FileSystemEventHandler):
    def __init__(self, bus: IfcBus, json_path: Path):
        self.bus = bus
        self.json_path = json_path
        self.last_modified = 0
    
    def on_modified(self, event):
        if event.src_path == str(self.json_path.resolve()):
            # Debounce: avoid multiple events for the same modification
            current_time = time.time()
            if current_time - self.last_modified > 1:
                print('\nJSON file changed, republishing...')
                self.publish_entities()
                self.last_modified = current_time
    
    def publish_entities(self):
        try:
            # Read JSON file
            with open(self.json_path) as f:
                data = json.load(f)
            
            print("\nPublishing entities...")
            # First pass: publish all entities
            entities = {}
            for entity_data in data["data"]:
                try:
                    # Keep all fields including type
                    entity_type = entity_data["type"]
                    entity_id = global_id_to_uuid(entity_data["globalId"])
                    
                    # Use the entire entity data
                    publish_data = entity_data.copy()
                    del publish_data["type"]  # Remove type as it's passed separately
                    
                    print(f"\nPublishing {entity_type} with ID {entity_id}")
                    print(f"Data: {publish_data}")
                    
                    # Publish entity
                    self.bus.publish_entity_with_id(entity_id, entity_type, publish_data)
                    entities[entity_id] = entity_type
                    time.sleep(0.5)  # Small delay between publishes
                    
                except Exception as e:
                    print(f"Error publishing entity {entity_data.get('globalId')}: {e}")
            
            # Second pass: add relationships
            print("\nAdding relationships...")
            for rel_data in data.get("relationships", []):
                try:
                    source_id = global_id_to_uuid(rel_data["source"])
                    target_id = global_id_to_uuid(rel_data["target"])
                    rel_type = rel_data["type"]
                    
                    if source_id in entities and target_id in entities:
                        print(f"Adding {rel_type} between {source_id} and {target_id}")
                        self.bus.add_relationship(
                            source_id,
                            rel_type,
                            target_id,
                            rel_data.get("data")
                        )
                        time.sleep(0.5)  # Small delay between relationships
                    else:
                        print(f"Cannot add relationship: source or target entity not found")
                        
                except Exception as e:
                    print(f"Error adding relationship: {e}")
            
            print("\nPublished entities:")
            for entity_id, entity_type in entities.items():
                entity = self.bus._registers.get(entity_id)
                if entity:
                    print(f"\n{entity_type} ({entity_id}):")
                    print(f"Data: {entity.data}")
                    print(f"Relationships: {entity.relationships}")
            
        except Exception as e:
            print(f'Error reading/parsing JSON: {e}')


def run_publish_mesh():
    """Run the mesh publishing example with file monitoring."""
    set_default_transport(MqttTransport(MQTT_HOST, MQTT_PORT))
    print("=== Starting Mesh Publisher with File Monitor ===")
    
    # Create bus instance and connect
    bus = IfcBus("ifc_demo_1")
    bus.connect()
    time.sleep(1)
    
    # Set up file path
    json_path = Path(__file__).parent.parent.parent / "message" / "example_message_wall_mesh.json"
    
    # Set up file monitoring
    event_handler = JsonFileHandler(bus, json_path)
    observer = Observer()
    observer.schedule(event_handler, str(json_path.parent), recursive=False)
    observer.start()
    
    # Initial publish
    print('\nInitial publish of entities...')
    event_handler.publish_entities()
    
    print(f'\nMonitoring {json_path.name} for changes...')
    print('Press Ctrl+C to stop')
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print('\nStopping file monitor...')
        bus.disconnect()
    
    observer.join()


if __name__ == "__main__":
    run_publish_mesh()





if __name__ == "__main__":
    run_publish_mesh()
