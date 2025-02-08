# Use Miniconda image
FROM continuumio/miniconda3

# Set working directory
WORKDIR /app

# Install dependencies using Conda
RUN conda install -c conda-forge python=3.9 ifcopenshell pytest black mypy rust

# Copy project files
COPY . .

# Install pip dependencies
RUN pip install --no-cache-dir compas_eve>=1.0.0 automerge==1.0.0rc1 python-dotenv>=1.0.0

# Build and install the local package
RUN python setup.py build install

# Set default environment variables
ENV MQTT_HOST=nanomq-broker
ENV MQTT_PORT=1883

# Run the Python script when the container starts
CMD ["python", "examples/mqtt_example.py"]