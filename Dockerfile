# Using develop branch for IsTemplate column of CSV
FROM ghcr.io/sage-bionetworks/synapsepythonclient:develop-fcf371f9bdeeaa8cf4ec0ea7c2446b7d20f35577

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
