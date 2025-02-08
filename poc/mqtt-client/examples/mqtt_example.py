"""Example demonstrating MQTT-based communication between IFC entities."""

from time import sleep
from uuid import uuid4
from ifc_databus.core.bus import IfcBus

from compas_eve import set_default_transport
from compas_eve.mqtt import MqttTransport



def run_mqtt_example():
    """Run the MQTT example."""
    set_default_transport(MqttTransport("localhost", 1883))

    print("=== Starting MQTT Example ===")
    
    # Create two bus instances
    bus_a = IfcBus("replica1")
    bus_b = IfcBus("replica2")
    
    # Connect to MQTT broker and wait for connections
    bus_a.connect()
    bus_b.connect()
    sleep(1)
    
    # Send sync messages to ensure both replicas are connected
    bus_a.publish_entity("IfcWall", {
        "name": "SyncWall",
        "height": 1.0,
        "width": 1.0,
    })
    bus_b.publish_entity("IfcWindow", {
        "name": "SyncWindow",
        "height": 1.0,
        "width": 1.0,
    })
    sleep(3)  # Increased delay to ensure sync
    
    # Create a wall in replica A
    wall_id = bus_a.publish_entity("IfcWall", {
        "name": "Wall1",
        "height": 3.0,
        "width": 2.0,
        "material": "Concrete",
    })
    sleep(5)  # Increased delay to ensure wall is synchronized
    
    # Create a window in replica B
    window_id = bus_b.publish_entity("IfcWindow", {
        "name": "Window1",
        "height": 1.2,
        "width": 0.8,
        "material": "Glass",
    })
    
    # Add relationship between wall and window
    bus_b.add_relationship(
        source_id=wall_id,
        rel_type="HasOpenings",
        target_id=window_id,
        rel_data={
            "position": "center",
            "offset_height": 1.0,
        }
    )
    sleep(5)  # Increased delay to ensure relationship is synchronized
    
    # Make concurrent modifications
    bus_a.update_entity(wall_id, {"height": 3.5})
    bus_b.update_entity(wall_id, {
        "material": "Reinforced Concrete",
        "thermal_resistance": 0.5,
    })
    sleep(5)  # Ensure updates are processed
    
    # Print final state
    wall_a = bus_a._registers[wall_id]
    print("\nFinal state:")
    print(f"Wall entity: {wall_a.entity_type}")
    print(f"Properties: {wall_a.data}")
    print(f"Relationships: {wall_a.relationships}")
    
    print("\nFinal state in Replica B:")
    wall_b = bus_b._registers[wall_id]
    print(f"Entity type: {wall_b.entity_type}")
    print(f"Data: {wall_b.data}")
    print(f"Relationships: {wall_b.relationships}")
    
    # Cleanup
    bus_a.disconnect()
    bus_b.disconnect()


if __name__ == "__main__":
    run_mqtt_example()
