"""Example demonstrating offline changes and syncing with Automerge."""
import json
import time
from pathlib import Path
from uuid import uuid4

from compas_eve import set_default_transport
from compas_eve.mqtt import MqttTransport
from config import MQTT_HOST, MQTT_PORT

from ifc_databus.core.bus import IfcBus
from ifc_databus.core.crdt_automerge import IfcRegister, ROOT


def inspect_crdt_data(register: IfcRegister, name: str = "Register"):
    """Inspect the internal state of an Automerge document."""
    print(f"\n=== {name} CRDT State ===")
    # Get the raw document state
    doc_state = register.doc.save()
    
    # Print document size
    print(f"Document size: {len(doc_state)} bytes")
    
    # Print document keys at ROOT
    print("\nRoot keys:")
    for key in register.doc.keys(ROOT):
        value = register.doc.get(ROOT, key)
        print(f"  {key}: {value}")
    
    # Print data fields
    print("\nData fields:")
    for key in register.doc.keys(register._data):
        value = register.doc.get(register._data, key)
        print(f"  {key}: {value}")
    
    # Print relationships
    print("\nRelationships:")
    for rel_type in register.doc.keys(register._rels):
        print(f"  {rel_type}:")
        rel_map_obj = register.doc.get(register._rels, rel_type)
        rel_map = rel_map_obj[1] if isinstance(rel_map_obj, tuple) else rel_map_obj
        for target_id in register.doc.keys(rel_map):
            rel_data_obj = register.doc.get(rel_map, target_id)
            print(f"    {target_id}: {rel_data_obj}")


def simulate_offline_changes():
    """Simulate offline changes in two replicas and then sync them."""
    # Create a wall entity
    wall_id = uuid4()
    wall_data = {
        "Name": "Basic Wall",
        "Description": "A simple wall",
        "Length": 5.0,
        "Height": 3.0,
    }

    # Create two offline replicas
    replica_a = IfcRegister.create_with_id(wall_id, "IfcWall", "replica_a", wall_data)
    replica_b = IfcRegister.create_with_id(wall_id, "IfcWall", "replica_b", wall_data)

    print("\n=== Initial State ===")
    print("Replica A:", json.dumps(replica_a.data, indent=2))
    print("Replica B:", json.dumps(replica_b.data, indent=2))
    
    # Inspect initial CRDT state
    inspect_crdt_data(replica_a, "Replica A Initial")

    # Make offline changes to replica A
    replica_a.update({
        "Length": 6.0,  # Changed length
        "Material": "Concrete",  # Added material
    })

    # Make offline changes to replica B
    replica_b.update({
        "Height": 4.0,  # Changed height
        "Thickness": 0.3,  # Added thickness
    })

    print("\n=== After Offline Changes ===")
    print("Replica A:", json.dumps(replica_a.data, indent=2))
    print("Replica B:", json.dumps(replica_b.data, indent=2))
    
    # Inspect CRDT state after changes
    inspect_crdt_data(replica_a, "Replica A After Changes")
    inspect_crdt_data(replica_b, "Replica B After Changes")

    # Save states to files
    offline_dir = Path("offline_states")
    offline_dir.mkdir(exist_ok=True)
    
    with open(offline_dir / "replica_a.bin", "wb") as f:
        f.write(replica_a.to_binary())
    with open(offline_dir / "replica_b.bin", "wb") as f:
        f.write(replica_b.to_binary())

    print("\nSaved offline states to files")
    return wall_id


def sync_offline_changes(wall_id):
    """Load offline states and sync them via MQTT."""
    # Configure MQTT transport
    transport = MqttTransport(host=MQTT_HOST, port=MQTT_PORT)
    set_default_transport(transport)

    # Create buses for both replicas
    bus_a = IfcBus("replica_a")
    bus_b = IfcBus("replica_b")

    # Load offline states
    offline_dir = Path("offline_states")
    with open(offline_dir / "replica_a.bin", "rb") as f:
        register_a = IfcRegister.from_binary(f.read(), "replica_a", wall_id)
    with open(offline_dir / "replica_b.bin", "rb") as f:
        register_b = IfcRegister.from_binary(f.read(), "replica_b", wall_id)

    # Add registers to buses
    bus_a._registers[wall_id] = register_a
    bus_b._registers[wall_id] = register_b

    # First sync attempt - this will show the partial sync issue
    print("\nFirst sync attempt...")
    bus_a.publish_entity_with_id(wall_id, register_a.entity_type, register_a.data)
    time.sleep(0.5)  # Small delay to ensure order
    bus_b.publish_entity_with_id(wall_id, register_b.entity_type, register_b.data)

    # Wait a bit and force a re-broadcast from both replicas
    time.sleep(2)
    print("\nForcing re-broadcast from both replicas...")
    bus_a._publish_message("broadcast", bus_a._registers[wall_id])
    time.sleep(0.5)
    bus_b._publish_message("broadcast", bus_b._registers[wall_id])

    # Wait for sync with progress updates
    print("\nWaiting for messages to propagate and merge...")
    for i in range(1, 6):  # Check state every second for 5 seconds
        time.sleep(1)
        print(f"\nState after {i} seconds:")
        print("Replica A:", json.dumps(bus_a._registers[wall_id].data, indent=2))
        print("Replica B:", json.dumps(bus_b._registers[wall_id].data, indent=2))

    print("\n=== Final Merged State ===")
    print("Replica A:", json.dumps(bus_a._registers[wall_id].data, indent=2))
    print("Replica B:", json.dumps(bus_b._registers[wall_id].data, indent=2))
    
    # Inspect final CRDT state
    inspect_crdt_data(bus_a._registers[wall_id], "Replica A Final")
    inspect_crdt_data(bus_b._registers[wall_id], "Replica B Final")


def run_offline_example():
    """Run the complete offline sync example."""
    print("=== Starting Offline Sync Example ===")
    
    # First simulate offline changes
    wall_id = simulate_offline_changes()
    
    # Then sync the changes
    sync_offline_changes(wall_id)


if __name__ == "__main__":
    run_offline_example()
