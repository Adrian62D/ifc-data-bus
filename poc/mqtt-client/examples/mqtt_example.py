"""Example demonstrating MQTT-based communication between IFC entities."""

import time
from time import sleep
from uuid import uuid4
from ifc_databus.core.bus import IfcBus

from compas_eve import set_default_transport
from compas_eve.mqtt import MqttTransport

def run_mqtt_example():
    """Run the MQTT example."""
    set_default_transport(MqttTransport("nanomq-broker", 1883))

    print("=== Starting MQTT Example ===")
    # Create two bus instances
    bus_a = IfcBus("replica1")
    bus_b = IfcBus("replica2")

    # Connect to MQTT broker and wait for connections
    bus_a.connect()
    bus_b.connect()
    sleep(1)

    run_integration(bus_a, bus_b)
    run_example(bus_a, bus_b)
    
    # Cleanup
    bus_a.disconnect()
    bus_b.disconnect()

def run_integration(bus_a, bus_b):
    # Example Object
    material_layerset_id = bus_a.publish_entity("IfcMaterialLayerSet", {
            "associatedTo": [
                {
                    "type": "IfcRelAssociatesMaterial",
                    "globalId": "8d0fbb28-fe53-488a-a92b-a5a3c1af7a74",
                    "name": "MatAssoc",
                    "description": "Material Associates",
                    "relatedObjects": [
                        {
                            "type": "IfcWallType",
                            "ref": "909e31f1-aec1-4242-8f2c-e2425a98a449"
                        }
                    ]
                }
            ],
            "materialLayers": [
                {
                    "type": "IfcMaterialLayer",
                    "material": {
                        "type": "IfcMaterial",
                        "name": "Masonry - Brick - Brown"
                    },
                    "layerThickness": 110.0,
                    "isVentilated": "false",
                    "name": "Finish"
                },
                {
                    "type": "IfcMaterialLayer",
                    "layerThickness": 50.0,
                    "isVentilated": "true",
                    "name": "Air Infiltration Barrier"
                },
                {
                    "type": "IfcMaterialLayer",
                    "material": {
                        "type": "IfcMaterial",
                        "name": "Masonry"
                    },
                    "layerThickness": 110.0,
                    "isVentilated": "false",
                    "name": "Core"
                }
            ],
            "layerSetName": "Double Brick - 270"
        }
    )
    sleep(5)  # Increased delay to ensure object is synchronized
    material_layerset_id = bus_a._registers[material_layerset_id]
    print("\nFinal state in Replica A:")
    print(f"Material Layer Set entity: {material_layerset_id.entity_type}")
    print(f"Properties: {material_layerset_id.data}")
    print(f"Relationships: {material_layerset_id.relationships}")

def wait_for_entity(bus, entity_id, timeout=10, interval=0.1):
    """Wait for an entity to exist in a bus replica."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if bus.has_entity(entity_id):
            return True
        sleep(interval)
    return False

def run_example(bus_a, bus_b):
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
    
    # Wait for wall to be synchronized to replica B
    if not wait_for_entity(bus_b, wall_id):
        raise TimeoutError("Timeout waiting for wall to sync to replica B")

    # Create a window in replica B
    window_id = bus_b.publish_entity("IfcWindow", {
        "name": "Window1",
        "height": 1.2,
        "width": 0.8,
        "material": "Glass",
    })
    
    # Wait for window to be synchronized
    if not wait_for_entity(bus_b, window_id):
        raise TimeoutError("Timeout waiting for window to sync")

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
    print("\nFinal state in Replica A:")
    print(f"Wall entity: {wall_a.entity_type}")
    print(f"Properties: {wall_a.data}")
    print(f"Relationships: {wall_a.relationships}")

    print("\nFinal state in Replica B:")
    wall_b = bus_b._registers[wall_id]
    print(f"Entity type: {wall_b.entity_type}")
    print(f"Data: {wall_b.data}")
    print(f"Relationships: {wall_b.relationships}")

if __name__ == "__main__":
    run_mqtt_example()
