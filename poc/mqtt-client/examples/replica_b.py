"""Example demonstrating MQTT-based communication for Replica B."""

from time import sleep
from uuid import UUID
from ifc_databus.core.bus import IfcBus

from compas_eve import set_default_transport
from compas_eve.mqtt import MqttTransport


def run_replica_b():
    """Run Replica B."""
    set_default_transport(MqttTransport("localhost", 1883))

    print("=== Starting Replica B ===")
    
    # Create bus instance
    bus_b = IfcBus("replica2")
    
    # Connect to MQTT broker and wait for connection
    bus_b.connect()
    sleep(1)
    
    # Send sync message
    wall_id = UUID("c231300d-58f7-4c82-ade7-cb328725f0d9")
    bus_b.publish_entity("IfcWindow", {
        "name": "SyncWindow",
        "height": 1.0,
        "width": 1.0,
    })
    sleep(3)  # Wait for sync
    print("Waiting for info from the other replicas")
    sleep(10)
    
    # Create a window
    window_id = bus_b.publish_entity("IfcWindow", {
        "name": "Window1",
        "height": 1.2,
        "width": 0.8,
        "material": "Glass",
    })
    print(f"\nCreated window with ID: {window_id}")
    
    # Add relationship between window and wall
    bus_b.add_relationship(
        source_id=wall_id,
        rel_type="HasOpenings",
        target_id=window_id,
        rel_data={
            "position": "center",
            "offset_height": 1.0,
        }
    )
    print("\nAdded relationship between wall and window")
    sleep(5)  # Wait for sync
    
    # Make modifications to wall
    bus_b.update_entity(wall_id, {
        "material": "Reinforced Concrete",
        "thermal_resistance": 0.5,
    })
    print("\nUpdated wall properties")
    sleep(5)  # Wait for updates
    
    # Print final state
    wall_b = bus_b._registers[wall_id]
    print("\nFinal state in Replica B:")
    print(f"Entity type: {wall_b.entity_type}")
    print(f"Data: {wall_b.data}")
    print(f"Relationships: {wall_b.relationships}")
    
    # Keep running to receive updates
    try:
        print("\nListening for updates (Press Ctrl+C to stop)...")
        while True:
            sleep(1)
    except KeyboardInterrupt:
        print("\nStopping Replica B...")
        bus_b.disconnect()


if __name__ == "__main__":
    run_replica_b()
