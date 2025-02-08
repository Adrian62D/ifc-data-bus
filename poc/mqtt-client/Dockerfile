# Use Miniconda image
FROM continuumio/miniconda3

# Set working directory
WORKDIR /app

# Install dependencies using Conda
RUN conda install -c conda-forge python=3.9 ifcopenshell pytest black mypy rust

# Copy project files
COPY . .

# Install pip dependencies
RUN pip install --no-cache-dir compas_eve>=1.0.0 automerge==1.0.0rc1

# Build and install the local package
RUN python setup.py build install

# Run the Python script when the container starts
CMD ["python", "examples/mqtt_example.py"]