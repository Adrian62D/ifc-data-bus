FROM python:3.9-slim

# Install MQTT client dependencies
RUN pip install paho-mqtt==2.1.0

# Set working directory
WORKDIR /app

# Copy Python script
COPY pub_sub.py .

# Run the script
CMD ["python", "pub_sub.py"]