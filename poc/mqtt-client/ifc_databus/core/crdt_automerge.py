"""CRDT implementations for IFC data using automerge-py."""
from typing import Any, Dict, Optional, Set
from uuid import UUID, uuid4
import time
from automerge.core import Document, ROOT, ObjType, ScalarType


class IfcRegister:
    """Generic CRDT register for any IFC entity using Automerge."""
    
    def __init__(
        self,
        id: UUID,
        entity_type: str,
        replica_id: str,
        doc: Optional[Document] = None,
    ):
        self.id = id
        if doc is None:
            self.doc = Document()
            with self.doc.transaction() as tx:
                self._data = tx.put_object(ROOT, "data", ObjType.Map)
                self._rels = tx.put_object(ROOT, "relationships", ObjType.Map)
                tx.put(ROOT, "entity_type", ScalarType.Str, entity_type)
                tx.put(ROOT, "replica_id", ScalarType.Str, replica_id)
                tx.put(ROOT, "timestamp", ScalarType.F64, time.time())
        else:
            self.doc = doc
            data_obj = self.doc.get(ROOT, "data")
            rels_obj = self.doc.get(ROOT, "relationships")
            self._data = data_obj[1] if isinstance(data_obj, tuple) else data_obj
            self._rels = rels_obj[1] if isinstance(rels_obj, tuple) else rels_obj
    
    @property
    def entity_type(self) -> str:
        return self.doc.get(ROOT, "entity_type")[0][1]
    
    @property
    def replica_id(self) -> str:
        return self.doc.get(ROOT, "replica_id")[0][1]
    
    @property
    def data(self) -> Dict[str, Any]:
        result = {}
        for key in self.doc.keys(self._data):
            value_tuple = self.doc.get(self._data, key)
            result[key] = value_tuple[0][1]  # ((ScalarType, value), bytes)
        return result
    
    @property
    def relationships(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        result = {}
        for rel_type in self.doc.keys(self._rels):
            rel_map_obj = self.doc.get(self._rels, rel_type)
            rel_map = rel_map_obj[1] if isinstance(rel_map_obj, tuple) else rel_map_obj
            result[rel_type] = {}
            for target_id in self.doc.keys(rel_map):
                rel_data_obj = self.doc.get(rel_map, target_id)
                rel_data = rel_data_obj[1] if isinstance(rel_data_obj, tuple) else rel_data_obj
                result[rel_type][target_id] = {
                    k: self.doc.get(rel_data, k)[0][1]  # Get the actual value
                    for k in self.doc.keys(rel_data)
                }
        return result
    
    @property
    def timestamp(self) -> float:
        return self.doc.get(ROOT, "timestamp")[0][1]
    
    @classmethod
    def create(cls, entity_type: str, replica_id: str, data: Dict[str, Any]) -> "IfcRegister":
        """Create a new IFC entity register with a random UUID."""
        return cls.create_with_id(uuid4(), entity_type, replica_id, data)
    
    @classmethod
    def create_with_id(cls, id: UUID, entity_type: str, replica_id: str, data: Dict[str, Any]) -> "IfcRegister":
        """Create a new IFC entity register with a specific UUID.
        
        This is useful when you want to preserve IDs from an existing IFC file.
        """
        register = cls(
            id=id,
            entity_type=entity_type,
            replica_id=replica_id,
        )
        with register.doc.transaction() as tx:
            for key, value in data.items():
                if isinstance(value, (int, float)):
                    scalar_type = ScalarType.F64
                elif isinstance(value, bool):
                    scalar_type = ScalarType.Boolean
                else:
                    scalar_type = ScalarType.Str
                    value = str(value)
                tx.put(register._data, key, scalar_type, value)
        return register
    
    def update(self, new_data: Dict[str, Any]) -> None:
        """Update entity data."""
        with self.doc.transaction() as tx:
            for key, value in new_data.items():
                if isinstance(value, (int, float)):
                    scalar_type = ScalarType.F64
                elif isinstance(value, bool):
                    scalar_type = ScalarType.Boolean
                else:
                    scalar_type = ScalarType.Str
                    value = str(value)
                tx.put(self._data, key, scalar_type, value)
            tx.put(ROOT, "timestamp", ScalarType.F64, time.time())
    
    def add_relationship(
        self, rel_type: str, target_id: UUID, rel_data: Dict[str, Any] = None
    ) -> None:
        """Add a relationship to another entity."""
        with self.doc.transaction() as tx:
            # Get or create the relationship type map
            if rel_type not in self.doc.keys(self._rels):
                rel_map = tx.put_object(self._rels, rel_type, ObjType.Map)
            else:
                rel_map_obj = self.doc.get(self._rels, rel_type)
                rel_map = rel_map_obj[1] if isinstance(rel_map_obj, tuple) else rel_map_obj
            
            # Create a map for the target
            target_map = tx.put_object(rel_map, str(target_id), ObjType.Map)
            
            # Add relationship data if provided
            if rel_data:
                for key, value in rel_data.items():
                    if isinstance(value, (int, float)):
                        scalar_type = ScalarType.F64
                        value = float(value)
                    elif isinstance(value, bool):
                        scalar_type = ScalarType.Boolean
                    else:
                        scalar_type = ScalarType.Str
                        value = str(value)
                    tx.put(target_map, key, scalar_type, value)
            
            tx.put(ROOT, "timestamp", ScalarType.F64, time.time())
    
    def remove_relationship(self, rel_type: str, target_id: UUID) -> None:
        """Remove a relationship to another entity."""
        with self.doc.transaction() as tx:
            if rel_type in self.doc.keys(self._rels):
                rel_map_obj = self.doc.get(self._rels, rel_type)
                rel_map = rel_map_obj[1] if isinstance(rel_map_obj, tuple) else rel_map_obj
                target_id_str = str(target_id)
                if target_id_str in self.doc.keys(rel_map):
                    tx.delete(rel_map, target_id_str)
                    if not self.doc.keys(rel_map):
                        tx.delete(self._rels, rel_type)
                    tx.put(ROOT, "timestamp", ScalarType.F64, time.time())
    
    def merge(self, other: "IfcRegister") -> None:
        """Merge with another register."""
        if other.id != self.id:
            raise ValueError("Cannot merge registers with different IDs")
        
        # Merge the documents
        self.doc.merge(other.doc)
        
        # Merge all fields from both documents
        merged_data = {**self.data, **other.data}
        merged_rels = {**self.relationships, **other.relationships}
        
        # Update the merged data
        with self.doc.transaction() as tx:
            # Update all data fields
            for key, value in merged_data.items():
                if isinstance(value, (int, float)):
                    scalar_type = ScalarType.F64
                elif isinstance(value, bool):
                    scalar_type = ScalarType.Boolean
                else:
                    scalar_type = ScalarType.Str
                    value = str(value)
                tx.put(self._data, key, scalar_type, value)
            
            # Update all relationships
            for rel_type, targets in merged_rels.items():
                for target_id, rel_data in targets.items():
                    if rel_type not in self.doc.keys(self._rels):
                        rel_map = tx.put_object(self._rels, rel_type, ObjType.Map)
                    else:
                        rel_map_obj = self.doc.get(self._rels, rel_type)
                        rel_map = rel_map_obj[1] if isinstance(rel_map_obj, tuple) else rel_map_obj
                    
                    target_map = tx.put_object(rel_map, target_id, ObjType.Map)
                    for key, value in rel_data.items():
                        if isinstance(value, (int, float)):
                            scalar_type = ScalarType.F64
                        elif isinstance(value, bool):
                            scalar_type = ScalarType.Boolean
                        else:
                            scalar_type = ScalarType.Str
                        tx.put(target_map, key, scalar_type, value)
            
            # Update timestamp to be the max of both timestamps
            tx.put(ROOT, "timestamp", ScalarType.F64, max(self.timestamp, other.timestamp))
    
    def to_binary(self) -> bytes:
        """Convert the register to binary format for transmission."""
        return self.doc.save()
    
    @classmethod
    def from_binary(cls, binary: bytes, replica_id: str, id: Optional[UUID] = None) -> "IfcRegister":
        """Create a register from binary data."""
        doc = Document.load(binary)
        return cls(
            id=id or uuid4(),
            entity_type=doc.get(ROOT, "entity_type")[0][1],
            replica_id=replica_id,
            doc=doc
        )
