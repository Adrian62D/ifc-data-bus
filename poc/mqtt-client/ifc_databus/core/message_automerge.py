"""Message definitions for IFC data bus using Automerge."""
from dataclasses import dataclass
from typing import Any, Dict, Optional
from uuid import UUID
from .crdt_automerge import IfcRegister


@dataclass
class IfcMessage:
    """Message for IFC data using Automerge."""
    id: UUID
    entity_type: str
    crdt_data: bytes  # Binary Automerge document
    replica_id: str
    timestamp: float
    parent_id: Optional[UUID] = None
    changeset_id: Optional[UUID] = None

    @classmethod
    def from_register(cls, register: IfcRegister) -> "IfcMessage":
        """Create a message from an IFC register."""
        return cls(
            id=register.id,
            entity_type=register.entity_type,
            crdt_data=register.to_binary(),
            replica_id=register.replica_id,
            timestamp=register.timestamp
        )

    def to_register(self) -> IfcRegister:
        """Create an IFC register from this message."""
        return IfcRegister.from_binary(self.crdt_data, self.replica_id, self.id)

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary format for MQTT."""
        # Create a register to get the current data
        register = self.to_register()
        
        # Get the data and relationships
        data = register.data
        relationships = register.relationships
        
        # Print for debugging
        print(f"Register data: {data}")
        print(f"Register relationships: {relationships}")
        
        # Create the message dictionary with parsed data
        msg_dict = {
            "id": str(self.id),
            "entity_type": self.entity_type,
            "replica_id": self.replica_id,
            "timestamp": self.timestamp,
            "parent_id": str(self.parent_id) if self.parent_id else None,
            "changeset_id": str(self.changeset_id) if self.changeset_id else None,
            "data": data,  # Include parsed data directly
            "relationships": relationships,
        }
        
        print(f"Message dict: {msg_dict}")
        return msg_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IfcMessage":
        """Create message from dictionary format from MQTT."""
        # Create a new register with the data
        register = IfcRegister.create(
            entity_type=data["entity_type"],
            replica_id=data["replica_id"],
            data=data.get("data", {})
        )
        
        # Set the ID to match the message
        register.id = UUID(data["id"])
        
        # Add any relationships
        for rel_type, targets in data.get("relationships", {}).items():
            for target_id, rel_data in targets.items():
                register.add_relationship(rel_type, UUID(target_id), rel_data)
        
        # Create message from register
        return cls(
            id=UUID(data["id"]),
            entity_type=data["entity_type"],
            crdt_data=register.to_binary(),
            replica_id=data["replica_id"],
            timestamp=data["timestamp"],
            parent_id=UUID(data["parent_id"]) if data.get("parent_id") else None,
            changeset_id=UUID(data["changeset_id"]) if data.get("changeset_id") else None,
        )
