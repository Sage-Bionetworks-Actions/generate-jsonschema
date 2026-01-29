FROM ghcr.io/sage-bionetworks/synapsepythonclient:v4.11.0

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir synapseclient[pandas,curator]

# Copy Python script
COPY src/generate_jsonschema_action.py /usr/local/bin/generate_jsonschema_action.py

# Set working directory to GitHub workspace
WORKDIR /github/workspace

# Set entrypoint to Python script
ENTRYPOINT ["python", "/usr/local/bin/generate_jsonschema_action.py"]
