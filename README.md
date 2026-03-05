# Generate JSON Schema Action

![Continuous Integration](https://github.com/sage-bionetworks/generate-jsonschema/actions/workflows/ci.yml/badge.svg)
![Linter](https://github.com/sage-bionetworks/generate-jsonschema/actions/workflows/linter.yml/badge.svg)

A GitHub Action to generate JSON Schema files from data models (CSV/JSONLD) using the Synapse Python Client curator extension.

This action is part of the DPE-1554 implementation for automated JSON Schema management in Synapse workflows.

## Features

- ✅ Generate JSON Schemas from CSV or JSONLD data models
- ✅ Filter schemas by specific data types
- ✅ Support for class_label and display_label modes
- ✅ Output schemas as both files and JSON for downstream processing
- ✅ Designed for CI/CD workflows and Pull Request validation
- ✅ Uses official Synapse Python Client Docker image

## Usage

### Basic Example

```yaml
name: Validate Data Model
on:
  pull_request:
    types:
      - opened
      - synchronize
      - labeled
    branches:
      - 'main'
    paths:
      - 'models/**'  # Only trigger when model files change

jobs:
  generate-schemas:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Generate JSON Schemas
        id: generate
        uses: sage-bionetworks/generate-jsonschema@v1
        with:
          data-model-source: ./models/data.model.csv
          # data-types omitted = generate all types

      - name: Upload schemas as artifacts
        uses: actions/upload-artifact@v4
        with:
          name: json-schemas
          path: ${{ steps.generate.outputs.schemas }}
```

### Generate Specific Schemas with Custom Labels

```yaml
- name: Generate Schemas for Specific Types
  id: generate
  uses: sage-bionetworks/generate-jsonschema@v1
  with:
    data-model-source: ./models/biospecimen.model.csv
    data-types: 'Patient,Biospecimen,Analysis'
    data-model-labels: 'display_label'
```

### With PR Comment Integration

This action can be combined with [mshick/add-pr-comment](https://github.com/mshick/add-pr-comment) to automatically post schema summaries to Pull Requests:

```yaml
name: Generate and Comment Schemas
on:
  pull_request:
    types:
      - opened
      - synchronize
      - labeled
    branches:
      - 'main'
    paths:
      - 'models/**'

jobs:
  generate-schemas:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
    steps:
      - uses: actions/checkout@v4

      - name: Generate JSON Schemas
        id: generate
        uses: sage-bionetworks/generate-jsonschema@v1
        with:
          data-model-source: ./models/data.model.csv

      - name: Format Schema Report
        id: format
        run: |
          python - <<'PYTHON'
          import json
          import sys

          schemas = json.loads('''${{ steps.generate.outputs.schemas-json }}''')

          # Build markdown report with collapsible sections
          report = "## Generated JSON Schemas\n\n"

          for schema in schemas:
              schema_name = schema.get('title', 'Unnamed Schema')
              schema_id = schema.get('$id', 'N/A')

              report += f"<details>\n<summary><strong>{schema_name}</strong></summary>\n\n"
              report += f"**Schema ID:** `{schema_id}`\n\n"

              # Add properties summary
              properties = schema.get('properties', {})
              if properties:
                  report += "**Properties:**\n"
                  for prop_name, prop_def in properties.items():
                      prop_type = prop_def.get('type', 'any')
                      required = '✓' if prop_name in schema.get('required', []) else ''
                      report += f"- `{prop_name}` ({prop_type}) {required}\n"

              report += "\n</details>\n\n"

          # Write to file
          with open('schema-report.md', 'w') as f:
              f.write(report)
          PYTHON

      - name: Comment PR with Schema Summary
        uses: mshick/add-pr-comment@v2
        with:
          message-path: schema-report.md
          message-id: schema-generation
```

The `schemas-json` output contains the full array of schema dictionaries, allowing you to create custom formatters and reports. The `message-id` parameter ensures the comment is "sticky" and will update on subsequent runs rather than creating multiple comments.

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `data-model-source` | Path or URL to CSV or JSONLD data model file | Yes | - |
| `data-types` | Comma-separated list of data types to generate schemas for (leave empty for all) | No | `''` |
| `data-model-labels` | Label type to use: `class_label` or `display_label` | No | `class_label` |

### About `data-model-labels`

- `class_label` (default): Uses standard attribute names as property keys
- `display_label`: Uses display names if valid (no blacklisted characters like parentheses, periods, spaces, or hyphens)

## Outputs

| Output | Description |
|--------|-------------|
| `schemas` | Path to directory containing generated schema files (e.g., `/workspace/schemas`) |
| `schemas-json` | JSON string containing array of generated schema dictionaries for use with PR comment actions or other downstream processing |

## Workflow Trigger Configuration (Recommended)

We recommend using specific workflow triggers to run this action only when relevant files change. This improves efficiency and reduces unnecessary CI runs.

### Recommended Trigger Configuration

```yaml
on:
  pull_request:
    types:
      - opened           # When PR is first opened
      - synchronize      # When new commits are pushed
      - labeled          # When labels are added (optional - useful for manual triggers)
    branches:
      - 'main'           # Only for PRs targeting main branch
    paths:
      - 'path/to/data/model/directories/**'      # Your data model directories
```

### Why These Triggers?

- **`types`**: Controls when the workflow runs during the PR lifecycle
  - `opened`: Validates schemas when PR is created
  - `synchronize`: Re-validates on new commits
  - `labeled`: Allows manual triggering by adding labels

- **`branches`**: Ensures the workflow only runs for PRs targeting your main branch

- **`paths`**: Prevents unnecessary runs when unrelated files change (e.g., documentation, tests)


## Local Development and Testing

### Running Unit Tests

Install dependencies and run tests:

```bash
# Install dependencies
pip install -r requirements.txt
pip install "synapseclient[pandas,curator] @ git+https://github.com/Sage-Bionetworks/synapsePythonClient@fcf371f9bdeeaa8cf4ec0ea7c2446b7d20f35577"
pip install pytest

# Run tests
pytest test -v
```

### Building the Docker Container

```bash
docker build -t generate-jsonschema-action .
```

### Testing with Docker

#### On Unix/macOS (bash):

```bash
docker run --rm \
  -e DATA_MODEL_SOURCE="/test/data.model.csv" \
  -v $(pwd)/test:/test \
  generate-jsonschema-action
```

#### On Windows (PowerShell):

Use backticks (`) for line continuation, and use `${PWD}` for the current directory. Use absolute Windows paths with forward slashes or double backslashes.

```powershell
docker run --rm `
  -e DATA_MODEL_SOURCE="/test/data.model.csv" `
  -v "${PWD}/test:/test" `
  generate-jsonschema-action
```

Or as a single line:

```powershell
docker run --rm -e DATA_MODEL_SOURCE="/test/data.model.csv" -v "${PWD}/test:/test" generate-jsonschema-action
```


## Technical Details

- **Base Image**: `ghcr.io/sage-bionetworks/synapsepythonclient:v4.11.0`
- **Python Version**: 3.10+
- **Dependencies**: synapseclient v4.11.0 with curator extension (pre-installed in base image)

## Related Actions

This action is designed to work with:
- [sage-bionetworks/register-jsonschema](https://github.com/sage-bionetworks/register-jsonschema) - Register generated schemas to Synapse organizations (coming soon)
- [mshick/add-pr-comment](https://github.com/mshick/add-pr-comment) - Post schema summaries to Pull Requests

## Documentation

- [Synapse Schema Operations Tutorial](https://python-docs.synapse.org/en/latest/tutorials/python/schema_operations/)
- [Synapse Curator Extension API Reference](https://python-docs.synapse.org/en/stable/reference/experimental/extensions/curator/)
- [Synapse Curator Extension Guide](https://python-docs.synapse.org/en/stable/guides/curator/)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

See [LICENSE](LICENSE) file for details.

## Support

For issues and questions:
- Open an issue in this repository
- Check the [Synapse documentation](https://python-docs.synapse.org/)
- Visit the [Sage Bionetworks community forums](https://www.synapse.org/)
