# The base image tag sets the synapseclient version.
FROM ghcr.io/sage-bionetworks/synapsepythonclient:v4.15.0

# Copy Python script
COPY src/generate_jsonschema_action.py /usr/local/bin/generate_jsonschema_action.py

# Set working directory to GitHub workspace
WORKDIR /github/workspace

# Set entrypoint to Python script
ENTRYPOINT ["python", "/usr/local/bin/generate_jsonschema_action.py"]
