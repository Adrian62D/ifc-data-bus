"""Validation rules for IFC entities and relationships."""
from typing import Dict, Any, Optional, Set
from dataclasses import dataclass, field


@dataclass
class EntityRule:
    """Rules for an IFC entity type."""
    required_fields: Set[str] = field(default_factory=set)
    allowed_fields: Set[str] = field(default_factory=set)
    allowed_relationships: Dict[str, Set[str]] = field(default_factory=dict)  # rel_type -> target_entity_types
    
    def __post_init__(self):
        """Add common fields that are allowed in all entities."""
        self.allowed_fields.add("type")
        self.allowed_fields.add("globalId")
        self.allowed_fields.add("description")
    
    def validate_data(self, data: Dict[str, Any]) -> Optional[str]:
        """Validate entity data against rules."""
        # Only check required fields
        for field in self.required_fields:
            if field not in data:
                return f"Missing required field: {field}"
        
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
    # Mesh-related entities
    "IfcTriangulatedFaceSet": EntityRule(
        required_fields={"coordinates", "coordIndex"},
        allowed_fields={"type", "coordinates", "coordIndex", "closed", "PnIndex"}
    ),
    "IfcCartesianPointList3D": EntityRule(
        required_fields={"coordList"},
        allowed_fields={"type", "coordList"}
    ),
    "IfcShapeRepresentation": EntityRule(
        required_fields={"representationIdentifier", "representationType", "items"},
        allowed_fields={"type", "representationIdentifier", "representationType", "items"}
    ),
    "IfcProductDefinitionShape": EntityRule(
        required_fields={"representations"},
        allowed_fields={"type", "representations"}
    ),
    "IfcLocalPlacement": EntityRule(
        required_fields={"relativePlacement"},
        allowed_fields={"type", "placementRelTo", "relativePlacement"}
    ),
    "IfcAxis2Placement3D": EntityRule(
        required_fields={"location"},
        allowed_fields={"type", "location", "axis", "refDirection"}
    ),
    "IfcCartesianPoint": EntityRule(
        required_fields={"coordinates"},
        allowed_fields={"type", "coordinates"}
    ),
    "IfcDirection": EntityRule(
        required_fields={"directionRatios"},
        allowed_fields={"type", "directionRatios"}
    ),
    "IfcPropertySet": EntityRule(
        required_fields={"name", "hasProperties"},
        allowed_fields={"type", "globalId", "name", "description", "hasProperties"}
    ),
    "IfcPropertySingleValue": EntityRule(
        required_fields={"name", "nominalValue"},
        allowed_fields={"type", "name", "description", "nominalValue"}
    ),
    "IfcText": EntityRule(
        required_fields={"value"},
        allowed_fields={"type", "value"}
    ),
    "IfcRelAssociates": EntityRule(
        required_fields={"relatedObjects", "relatingPropertyDefinition"},
        allowed_fields={"type", "globalId", "name", "relatedObjects", "relatingPropertyDefinition"}
    ),
    "IfcClassificationReference": EntityRule(
        required_fields={"identification", "name"},
        allowed_fields={"type", "globalId", "identification", "name", "description", "location"}
    ),
    "IfcRelAssociatesClassification": EntityRule(
        required_fields={"type", "relatedObjects"},
        allowed_fields={"type", "globalId", "name", "description", "relatedObjects", "relatingClassification"}
    ),
    "IfcWall": EntityRule(
        required_fields={},
        allowed_fields={
            "globalId", "data",
            "name", "height", "width", "materialLayers", "layerSetName",
            "thermal_resistance", "relatedObjects", "material",
            "objectPlacement", "representation"
        },
        allowed_relationships={
            "HasOpenings": {"IfcWindow", "IfcDoor"},
            "connects": {"IfcWall"},
            "bounds": {"IfcSpace"},
            "associatedTo": {"IfcRelAssociatesMaterial"},
        }
    ),
    "IfcWall_data": EntityRule(
        required_fields={"type", "version", "schemaIdentifier", "data"},
        allowed_fields={"type", "version", "schemaIdentifier", "data"}
    ),
    "IfcMaterialLayerSet": EntityRule(
        required_fields={"associatedTo", "materialLayers", "layerSetName"},
        allowed_fields={"associatedTo", "materialLayers", "layerSetName"}
    ),
    "IfcRelAssociatesMaterial": EntityRule(
        required_fields={"type", "relatedObjects"},
        allowed_fields={"type", "globalId", "name", "description", "relatedObjects", "relatingMaterial"}
    ),
    "IfcWallType": EntityRule(
        required_fields={"type", "ref"},
        allowed_fields={"type", "ref"}
    ),
    "IfcMaterialLayer": EntityRule(
        required_fields={"type", "layerThickness", "isVentilated", "name"},
        allowed_fields={"type", "layerThickness", "isVentilated", "name", "material"}
    ),
    "IfcMaterial": EntityRule(
        required_fields={"type", "name"},
        allowed_fields={"type", "name"}
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
