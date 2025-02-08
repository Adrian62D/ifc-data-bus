"""Core bus implementation using MQTT."""
from typing import Any, Callable, Dict, Optional
from uuid import UUID, uuid4
import json
import base64
from datetime import datetime
from pathlib import Path
import getpass

from compas_eve import Publisher, Subscriber, Topic, Message
from .message_automerge import IfcMessage
from .crdt_automerge import IfcRegister
from .validation import validate_entity, validate_relationship


class IfcBus:
    """Main IFC data bus implementation."""
    
    def __init__(self, replica_id: str = None):
        self.replica_id = replica_id or str(uuid4())
        self._publishers: Dict[str, Publisher] = {}
        self._subscribers: Dict[str, Subscriber] = {}
        self._callbacks: Dict[str, list] = {}
        self._registers: Dict[UUID, IfcRegister] = {}
        
        # Create logs directory if it doesn't exist
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        self.log_file = self.log_dir / f"mqtt_messages_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        # Subscribe to all IFC topics once
        self._subscribe_to_all_entities()
        
    def connect(self):
        """Connect to the message bus."""
        for pub in self._publishers.values():
            pub.advertise()
        for sub in self._subscribers.values():
            sub.subscribe()
        
    def disconnect(self):
        """Disconnect from the message bus."""
        for pub in self._publishers.values():
            pub.unadvertise()
        for sub in self._subscribers.values():
            sub.unsubscribe()
        
    def has_entity(self, entity_id: UUID) -> bool:
        """Check if an entity exists in this replica."""
        return entity_id in self._registers
    
    def publish_entity(self, entity_type: str, data: Dict[str, Any]) -> UUID:
        """Publish an IFC entity with a random UUID."""
        # Generate a new UUID
        id = uuid4()
        return self.publish_entity_with_id(id, entity_type, data)
    
    def publish_entity_with_id(self, id: UUID, entity_type: str, data: Dict[str, Any]) -> UUID:
        """Publish an IFC entity with a specific UUID.
        
        This is useful when you want to preserve IDs from an existing IFC file.
        """
        # Validate entity data
        error = validate_entity(entity_type, data)
        if error:
            raise ValueError(error)
            
        # Create entity register
        entity = IfcRegister.create_with_id(id, entity_type, self.replica_id, data)
        self._registers[entity.id] = entity
        
        # Publish the register
        self._publish_message("create", entity)
        
        return entity.id
    
    def update_entity(self, entity_id: UUID, data: Dict[str, Any]):
        """Update an existing entity."""
        if entity_id not in self._registers:
            raise ValueError(f"Entity {entity_id} not found")
            
        # Validate updated data
        entity = self._registers[entity_id]
        error = validate_entity(entity.entity_type, {**entity.data, **data})
        if error:
            raise ValueError(error)
            
        # Update entity register
        entity.update(data)
        
        # Publish the register
        self._publish_message("update", entity)
    
    def add_relationship(self, source_id: UUID, rel_type: str, target_id: UUID, rel_data: Dict[str, Any] = None):
        """Add a relationship between entities."""
        if source_id not in self._registers:
            raise ValueError(f"Source entity {source_id} not found")
        if target_id not in self._registers:
            raise ValueError(f"Target entity {target_id} not found")
            
        # Validate relationship
        source = self._registers[source_id]
        target = self._registers[target_id]
        error = validate_relationship(source.entity_type, rel_type, target.entity_type)
        if error:
            raise ValueError(error)
        
        # Add relationship
        source.add_relationship(rel_type, target_id, rel_data)
        
        # Publish the register
        self._publish_message("add_relationship", source)
    
    def _publish_message(self, operation_type: str, register: IfcRegister):
        """Publish an IFC register."""
        # Get topic for this entity type
        topic_name = f"ifc/{register.entity_type}"
        
        # Create publisher if needed
        if topic_name not in self._publishers:
            topic = Topic(topic_name)
            self._publishers[topic_name] = Publisher(topic)
            self._publishers[topic_name].advertise()
            print(f"Created new publisher for {topic_name}")
        
        # Convert register to dict for MQTT
        msg_dict = {
            "operation_type": operation_type,
            "operation_id": str(uuid4()),
            "author": getpass.getuser(),
            "id": str(register.id),
            "entity_type": register.entity_type,
            "replica_id": self.replica_id,  # Use our replica ID
            "timestamp": register.timestamp,
            "data": register.data,
            "relationships": register.relationships,
            "crdt_data": base64.b64encode(register.to_binary()).decode('utf-8'),  # Include CRDT data
        }

        # Publish message
        msg = Message(msg_dict)
        self._publishers[topic_name].publish(msg)
        print(f"Published message to {topic_name} with data: {register.data}")
        
        # Log the message
        with open(self.log_file, "a") as f:
            f.write(json.dumps(msg_dict) + "\n")
        
    def _handle_message(self, message: Message):
        """Handle incoming messages."""
        try:
            # Get payload from message
            payload = message.data
            
            # Skip our own messages
            if payload.get("replica_id") == self.replica_id:
                return
            
            # Get message ID and CRDT data
            msg_id = UUID(payload["id"])
            crdt_data = base64.b64decode(payload["crdt_data"].encode('utf-8'))
            
            # Create or update register using CRDT data
            incoming_register = IfcRegister.from_binary(crdt_data, payload["replica_id"], msg_id)
            print(f"Received data: {incoming_register.data} from {payload['replica_id']}")
            
            if msg_id not in self._registers:
                # Create new register
                self._registers[msg_id] = incoming_register
                print(f"Created new register for {msg_id}")
            else:
                # Get the current register
                current_register = self._registers[msg_id]
                print(f"Current data: {current_register.data}")
                
                # Always merge CRDT data
                old_data = current_register.data.copy()
                current_register.merge(incoming_register)
                print(f"Merged data: {current_register.data}")
                
                # Re-broadcast if data changed
                if current_register.data != old_data:
                    print(f"Re-broadcasting changes for {msg_id}")
                    self._publish_message("broadcast", current_register)
        except Exception as e:
            print(f"Error handling message: {e}")
        
    def _subscribe_to_all_entities(self):
        """Subscribe to all IFC entity topics."""
        entity_types = ["IfcWall", "IfcWindow", "IfcDoor"]
        for entity_type in entity_types:
            topic_name = f"ifc/{entity_type}"
            if topic_name not in self._subscribers:
                topic = Topic(topic_name)
                self._subscribers[topic_name] = Subscriber(
                    topic,
                    self._handle_message
                )
                self._subscribers[topic_name].subscribe()
                print(f"Created new subscriber for {topic_name}")
