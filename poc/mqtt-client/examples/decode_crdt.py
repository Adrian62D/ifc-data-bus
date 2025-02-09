#!/usr/bin/env python3
import base64
import sys
from uuid import uuid4
from ifc_databus.core.crdt_automerge import IfcRegister

def decode_crdt_data(crdt_data_str: str):
    """Decode and inspect a base64-encoded CRDT data string."""
    try:
        # Decode base64 string to bytes
        crdt_bytes = base64.b64decode(crdt_data_str.encode('utf-8'))
        
        # Create a temporary register to decode the data
        register = IfcRegister.from_binary(crdt_bytes, "decoder", uuid4())
        
        # Get document internals
        doc = register.doc
        
        print("\n=== CRDT Document Structure ===")
        print(f"\nEntity Type: {register.entity_type}")
        print(f"Timestamp: {register.timestamp}")
        
        # Get state information
        state = doc.save()
        print(f"\nDocument State:")
        print(f"  Size: {len(state)} bytes")
        
        # Get actor information
        actor = doc.get_actor()
        print(f"\nActor Information:")
        print(f"  ID: {actor.hex() if actor else 'None'}")
        
        # Get heads (version vectors)
        heads = doc.get_heads()
        print(f"\nHeads (Version Vectors):")
        for i, head in enumerate(heads, 1):
            print(f"  Head {i}: {head.hex()}")
        
        print(f"\nData fields:")
        for key, value in register.data.items():
            print(f"  {key}: {value}")
        
        print("\nRelationships:")
        for rel_type, targets in register.relationships.items():
            print(f"  {rel_type}:")
            for target_id, rel_data in targets.items():
                print(f"    {target_id}: {rel_data}")
        
    except Exception as e:
        print(f"Error decoding CRDT data: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python decode_crdt.py <base64-encoded-crdt-data>")
        sys.exit(1)
    
    decode_crdt_data(sys.argv[1])
