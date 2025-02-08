"""Validation rules for IFC entities and relationships."""
from typing import Dict, Any, Optional, Set
from dataclasses import dataclass, field


@dataclass
class EntityRule:
    """Rules for an IFC entity type."""
    required_fields: Set[str] = field(default_factory=set)
    allowed_fields: Set[str] = field(default_factory=set)
    allowed_relationships: Dict[str, Set[str]] = field(default_factory=dict)  # rel_type -> target_entity_types
    
    def validate_data(self, data: Dict[str, Any]) -> Optional[str]:
        """Validate entity data against rules."""
        # Check required fields
        for field in self.required_fields:
            if field not in data:
                return f"Missing required field: {field}"
        
        # Check field types and values (can be extended)
        for field, value in data.items():
            if field not in self.allowed_fields and field not in self.required_fields:
                return f"Unknown field: {field}"
        
        return None
    
    def validate_relationship(self, rel_type: str, target_type: str) -> Optional[str]:
        """Validate a relationship type with a target entity type."""
        if rel_type not in self.allowed_relationships:
            return f"Invalid relationship type: {rel_type}"
        
        allowed_targets = self.allowed_relationships[rel_type]
        if target_type not in allowed_targets:
            return f"Invalid target type for relationship {rel_type}: expected one of {allowed_targets}, got {target_type}"
        
        return None


# Define validation rules for common IFC entities
IFC_RULES: Dict[str, EntityRule] = {
    "IfcWall": EntityRule(
        required_fields={"name", "height", "width"},
        allowed_fields={"name", "height", "width", "material", "thermal_resistance"},
        allowed_relationships={
            "HasOpenings": {"IfcWindow", "IfcDoor"},
            "connects": {"IfcWall"},
            "bounds": {"IfcSpace"}
        }
    ),
    "IfcWindow": EntityRule(
        required_fields={"name", "height", "width"},
        allowed_fields={"name", "height", "width", "material"},
        allowed_relationships={
            "fills": {"IfcWall"},
            "hosts": {"IfcWindowStyle"}
        }
    ),
    "IfcSpace": EntityRule(
        required_fields={"Area"},
        allowed_fields={"Name", "Description", "Area", "Height", "Volume"},
        allowed_relationships={
            "bounded_by": {"IfcWall"},
            "contains": {"IfcWindow", "IfcDoor", "IfcFurnishingElement"}
        }
    ),
    "IfcDoor": EntityRule(
        required_fields={"Width", "Height"},
        allowed_fields={"Name", "Description", "Width", "Height", "Thickness", "Position"},
        allowed_relationships={
            "fills": {"IfcWall"},
            "hosts": {"IfcDoorStyle"}
        }
    )
}


def validate_entity(entity_type: str, data: Dict[str, Any]) -> Optional[str]:
    """Validate an IFC entity's data."""
    if entity_type not in IFC_RULES:
        return f"Unknown entity type: {entity_type}"
    
    return IFC_RULES[entity_type].validate_data(data)


def validate_relationship(source_type: str, rel_type: str, target_type: str) -> Optional[str]:
    """Validate a relationship between two IFC entities."""
    if source_type not in IFC_RULES:
        return f"Unknown source entity type: {source_type}"
    
    return IFC_RULES[source_type].validate_relationship(rel_type, target_type)
