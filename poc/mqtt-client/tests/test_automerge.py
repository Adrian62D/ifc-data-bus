"""Test the automerge CRDT implementation."""
from uuid import uuid4
from ifc_databus.core.crdt_automerge import IfcRegister

def test_basic_operations():
    """Test basic CRDT operations."""
    # Create two replicas
    replica1 = IfcRegister.create(
        entity_type="IfcWall",
        replica_id="replica1",
        data={"name": "Wall1", "height": 3.0}
    )
    
    # Create a second replica from the first one's binary data
    binary_data = replica1.to_binary()
    replica2 = IfcRegister.from_binary(binary_data, "replica2", replica1.id)
    
    # Make concurrent changes
    replica1.update({"width": 2.0, "material": "Concrete"})
    replica2.update({"width": 2.5, "color": "White"})
    
    # Merge changes
    replica1.merge(replica2)
    
    # Print final state
    print("\nReplica 1 final state:")
    print(f"Entity type: {replica1.entity_type}")
    print(f"Data: {replica1.data}")
    
    # Add relationships
    door_id = uuid4()
    replica1.add_relationship("HasOpenings", door_id, {"position": "center"})
    print(f"\nRelationships: {replica1.relationships}")

if __name__ == "__main__":
    test_basic_operations()
