import json
import re

import re

def parse_composite_file(file_path):
    composites = []
    current_composite = None
    
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        
    for line in lines:
        # Remove leading and trailing whitespace from the line
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
            
        # Skip the first line with number of composites
        if line.startswith("Number of composites:"):
            continue
            
        # New composite
        if line.startswith("Composite"):
            if current_composite:
                composites.append(current_composite)
            
            # Extract composite name
            composite_name = line.split(": ")[1]
            current_composite = {
                "name": composite_name,
                "layers": []
            }
            
        # Layer information
        elif line.startswith("  Layer"):
            thickness = float(re.search(r"Thickness = ([\d.]+)", line).group(1))
            
        # Material information
        elif line.startswith("    Material"):
            material_info = re.match(r"    Material (.*): Density = (\d+)", line)
            material_name = material_info.group(1)
            density = int(material_info.group(2))
            
            # Add layer to current composite
            current_composite["layers"].append({
                "thickness": thickness,
                "material": material_name,
                "density": density
            })
    
    # Add the last composite
    if current_composite:
        composites.append(current_composite)
  
    return composites


def generate_ifc_json(composites):
    ifc_json = {
        "type": "ifcJSON",
        "version": "0.0.1",
        "schemaIdentifier": "IFC4",
        "originatingSystem": "Custom Encoder",
        "preprocessorVersion": "1.0.0",
        "timeStamp": "2023-10-31T12:00:00",
        "data": []
    }

    for composite in composites:
        material_layers = []
        for layer in composite["layers"]:
            # Create material layer following the exact format from the reference
            material_layer = {
                "type": "IfcMaterialLayer",
                "material": {
                    "type": "IfcMaterial",
                    "name": layer["material"]
                } if layer["material"] else None,
                "layerThickness": layer["thickness"],
                "isVentilated": False,
                "name": f"Layer of {layer['material']}"
            }
            material_layers.append(material_layer)

        # Create material layer set
        material_layer_set = {
            "type": "IfcMaterialLayerSet",
            "materialLayers": material_layers,
            "layerSetName": composite["name"]
        }

        # Add to the main data array
        ifc_json["data"].append(material_layer_set)

    return ifc_json

# Main execution
def main(input_file_path, output_file_path):
    # Parse the input file
    composites = parse_composite_file(input_file_path)
    print(composites)
    
    # Generate IFC JSON
    ifc_json = generate_ifc_json(composites)

    # Save to file
    with open(output_file_path, 'w', encoding='utf-8') as f:
        json.dump(ifc_json, f, indent=4)


# Example usage
input_file = "/Users/matteodopudi/Downloads/sample_test_file.txt"
output_file = "/Users/matteodopudi/Desktop/composite_materials.json"
main(input_file, output_file)