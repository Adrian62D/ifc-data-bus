"""Example demonstrating MQTT-based communication for Replica A."""

from time import sleep
from uuid import UUID
from ifc_databus.core.bus import IfcBus

from compas_eve import set_default_transport
from compas_eve.mqtt import MqttTransport
from config import MQTT_HOST, MQTT_PORT


def run_replica_a():
    """Run Replica A."""
    set_default_transport(MqttTransport(MQTT_HOST, MQTT_PORT))

    print("=== Starting Replica A ===")
    
    # Create bus instance
    bus_a = IfcBus("replica1")
    
    # Connect to MQTT broker and wait for connection
    bus_a.connect()
    sleep(1)
    
    # Send sync message
    bus_a.publish_entity("IfcWall", {
        "name": "SyncWall",
        "height": 1.0,
        "width": 1.0,
    })
    sleep(3)  # Wait for sync
    
    # Create a wall
    wall_id = UUID("c231300d-58f7-4c82-ade7-cb328725f0d9")
    wall_id = bus_a.publish_entity_with_id(wall_id, "IfcWall", {
        "name": "Wall1",
        "height": 3.0,
        "width": 2.0,
        "material": "Concrete",
    })
    print(f"\nCreated wall with ID: {wall_id}")
    sleep(5)  # Wait for sync
    
    # Make modifications
    bus_a.update_entity(wall_id, {"height": 3.5})
    print("\nUpdated wall height to 3.5")
    sleep(5)  # Wait for updates
    
    # Print final state
    wall_a = bus_a._registers[wall_id]
    print("\nFinal state in Replica A:")
    print(f"Wall entity: {wall_a.entity_type}")
    print(f"Properties: {wall_a.data}")
    print(f"Relationships: {wall_a.relationships}")
    
    # Keep running to receive updates
    try:
        print("\nListening for updates (Press Ctrl+C to stop)...")
        while True:
            sleep(1)
    except KeyboardInterrupt:
        print("\nStopping Replica A...")
        bus_a.disconnect()


if __name__ == "__main__":
    run_replica_a()
