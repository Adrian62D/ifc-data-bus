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
mamba init
source ~/.bashrc
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

4. Configure environment variables:
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your settings
vim .env  # or use any text editor
```

5. Run examples:
```bash
cd examples
python mqtt_example.py
```

### Environment Variables

The following environment variables can be configured in your `.env` file:

- `MQTT_HOST`: MQTT broker hostname (default: "localhost")
- `MQTT_PORT`: MQTT broker port (default: 1883)

For Docker environments, these are automatically set in the docker-compose.yml file.

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
