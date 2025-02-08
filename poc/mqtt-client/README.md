# IFC Databus

A data bus implementation for IFC data using publisher/subscriber communication patterns.



## Features

- Publisher/Subscriber pattern using MQTT (over [`compas_eve`](https://github.com/compas-dev/compas_eve))
- Git-like changeset semantics for IFC data
- Support for hierarchical IFC data structures
- Initial focus on IfcWall entities

## Installation

This project uses `conda/mamba` for environment management. To get started:

0. Install Mamba:
```bash
brew install --cask mambaforge
```

1. Create the environment:
```bash
mamba env create -f environment.yml
```

2. Activate the environment:
```bash
mamba activate ifc-databus
```

3. create the package:
```bash
python setup.py build install
```

4. run some examples
```bash
cd examples
python mqtt_example.py 
```

## Development

1. Run tests:
```bash
pytest
```

2. Format code:
```bash
black .
```

## License

TBD
