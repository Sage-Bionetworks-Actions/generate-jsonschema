FROM ghcr.io/sage-bionetworks/synapsepythonclient:v4.11.0

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir synapseclient[pandas,curator]

# Set working directory
WORKDIR /usr/src

# Copy Python script
COPY src/generate_jsonschema_action.py .

# Set entrypoint to Python script
ENTRYPOINT ["python", "/usr/src/generate_jsonschema_action.py"]
