"""Test the raw automerge API."""
from automerge.core import Document, ROOT, ObjType, ScalarType

def test_basic_operations():
    """Test basic operations with raw automerge."""
    # Create a document
    doc = Document()
    with doc.transaction() as tx:
        data = tx.put_object(ROOT, "data", ObjType.Map)
        print(f"\nData object ID: {data}")
        print(f"Data type: {type(data)}")
        
        tx.put(data, "name", ScalarType.Str, "Wall1")
        tx.put(data, "height", ScalarType.F64, 3.0)
    
    # Print initial state
    print("\nInitial state:")
    data_obj = doc.get(ROOT, "data")
    print(f"Data object from get: {data_obj}")
    print(f"Data object type: {type(data_obj)}")
    
    # Make changes
    with doc.transaction() as tx:
        tx.put(data, "width", ScalarType.F64, 2.0)
    
    # Print final state
    print("\nFinal state:")
    for key in doc.keys(data):
        value = doc.get(data, key)
        print(f"{key}: {value}")

if __name__ == "__main__":
    test_basic_operations()
