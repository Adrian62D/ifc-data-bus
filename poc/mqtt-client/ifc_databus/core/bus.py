"""Core bus implementation using MQTT."""
from typing import Any, Callable, Dict, Optional
from uuid import UUID
import json
from datetime import datetime
from pathlib import Path

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
        
        # Subscribe to all IFC topics
        self.subscribe_to_entity("IfcWall", self._handle_message)
        self.subscribe_to_entity("IfcWindow", self._handle_message)
        self.subscribe_to_entity("IfcDoor", self._handle_message)
        
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
        
    def publish_entity(self, entity_type: str, data: Dict[str, Any]) -> UUID:
        """Publish an IFC entity."""
        # Validate entity data
        error = validate_entity(entity_type, data)
        if error:
            raise ValueError(error)
            
        # Create entity register
        entity = IfcRegister.create(entity_type, self.replica_id, data)
        self._registers[entity.id] = entity
        
        # Create and publish message
        message = IfcMessage.from_register(entity)
        self._publish_message(message)
        
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
        
        # Create and publish message
        message = IfcMessage.from_register(entity)
        self._publish_message(message)
    
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
        
        # Create and publish message
        message = IfcMessage.from_register(source)
        self._publish_message(message)
    
    def _publish_message(self, message: IfcMessage):
        """Publish an IFC message."""
        # First update our own register
        if message.id not in self._registers:
            # Create new register from message
            self._registers[message.id] = message.to_register()
            print(f"Created new register for {message.id}")
        else:
            # Merge with existing register
            register = self._registers[message.id]
            register.merge(message.to_register())
            print(f"Updated register for {message.id}")
        
        # Then publish to others
        topic_name = f"ifc/{message.entity_type}"
        if topic_name not in self._publishers:
            topic = Topic(topic_name)
            self._publishers[topic_name] = Publisher(topic)
            self._publishers[topic_name].advertise()
            print(f"Created new publisher for {topic_name}")
        
        # Convert message to dict for MQTT
        msg_dict = message.to_dict()
        msg = Message(msg_dict)
        self._publishers[topic_name].publish(msg)
        print(f"Published message to {topic_name}")
        
        # Log the message
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "topic": topic_name,
            "replica_id": self.replica_id,
            "message": msg_dict
        }
        with open(self.log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        
    def _handle_message(self, topic: Topic, message: Message):
        """Handle incoming messages."""
        try:
            print(f"Received message on topic {topic.name}")
            
            # Get payload from message
            payload = message.data
            # print(f"Message payload: {payload}")
            
            # Create message from payload
            message = IfcMessage.from_dict(payload)
            print(f"Created message object for {message.id}")
            
            # Convert to register and merge
            if message.id not in self._registers:
                self._registers[message.id] = message.to_register()
                print(f"Created new register for {message.id}")
            else:
                register = self._registers[message.id]
                old_state = register.to_binary()
                register.merge(message.to_register())
                new_state = register.to_binary()
                print(f"Updated register for {message.id}")
                
                # Only broadcast if there were actual changes and message is from another replica
                if old_state != new_state and payload.get("replica_id") != self.replica_id:
                    print(f"Broadcasting changes for {message.id}")
                    self._publish_message(IfcMessage(
                        id=message.id,
                        entity_type=register.entity_type,
                        crdt_data=new_state,
                        replica_id=self.replica_id,
                        timestamp=register.timestamp
                    ))
        except Exception as e:
            print(f"Error handling message: {e}")
        
    def subscribe_to_entity(self, entity_type: str, callback: Callable[[Topic, Message], None]):
        """Subscribe to messages for a specific entity type."""
        print(f"Subscribing to {entity_type} messages")
        
        # Subscribe to messages for this entity type
        topic_name = f"ifc/{entity_type}"
        if topic_name not in self._subscribers:
            topic = Topic(topic_name)
            self._subscribers[topic_name] = Subscriber(
                topic,
                lambda msg: self._handle_message(topic, msg)
            )
            self._subscribers[topic_name].subscribe()
            print(f"Created new subscriber for {topic_name}")
