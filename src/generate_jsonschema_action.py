#!/usr/bin/env python3
"""GitHub Action to generate JSON schemas from data models using synapseclient."""

import os
import sys
import json
from pathlib import Path
from synapseclient import Synapse
from synapseclient.extensions.curator import generate_jsonschema

VALID_DATA_MODEL_LABELS = ['class_label', 'display_label']
DEFAULT_DATA_MODEL_LABEL = 'class_label'
DEFAULT_OUTPUT_DIRECTORY = 'schemas'


def main() -> int:
    """
    Main function to generate JSON schemas from data models.

    Expects the following environment variables:
    - DATA_MODEL_SOURCE: URL or local path to the data model file (required)
    - DATA_TYPES: Comma-separated list of data types to include (optional, defaults to all)
    - DATA_MODEL_LABELS: 'class_label' or 'display_label' for schema
    - OUTPUT_DIRECTORY: Directory to output generated schema files (optional, defaults to 'schemas')
    - GITHUB_OUTPUT: Path to GitHub Actions output file (automatically provided in GitHub Actions environment)
    """
    data_model_source = os.environ.get('DATA_MODEL_SOURCE')
    if not data_model_source:
        print("::error::DATA_MODEL_SOURCE is required", file=sys.stderr)
        return 1

    # Validate data model file exists (if local path)
    if not data_model_source.startswith(('http://', 'https://')):
        data_model_path = Path(data_model_source)
        if not data_model_path.exists():
            print(
                f"::error::Data model file not found: {data_model_source}",
                file=sys.stderr
            )
            return 1

    # Parse data_types: empty string means all types (None)
    data_types_str = os.environ.get('DATA_TYPES')
    if data_types_str:
        # Split, strip, and filter out empty strings
        data_types = [dt.strip() for dt in data_types_str.split(',') if dt.strip()]
    else:
        # If DATA_TYPES is not set or is an empty string, synapseclient generates for all types
        data_types = None

    # Validate data_model_labels
    data_model_labels = os.environ.get('DATA_MODEL_LABELS', DEFAULT_DATA_MODEL_LABEL)
    if data_model_labels not in VALID_DATA_MODEL_LABELS:
        print(
            f"::warning::Invalid data_model_labels '{data_model_labels}', "
            f"using '{DEFAULT_DATA_MODEL_LABEL}'"
        )
        data_model_labels = DEFAULT_DATA_MODEL_LABEL

    # Create output directory relative to current working directory
    # This ensures it's created in the GitHub workspace where artifacts can be uploaded
    output_dir_name = os.environ.get('OUTPUT_DIRECTORY', DEFAULT_OUTPUT_DIRECTORY)
    output_dir = os.path.join(os.getcwd(), output_dir_name)
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n{'='*60}")
    print("JSON Schema Generation")
    print(f"{'='*60}")
    print(f"Data Model Source: {data_model_source}")
    print(f"Data Types: {data_types}")
    print(f"Data Model Labels: {data_model_labels}")
    print(f"Output Directory: {output_dir}")
    print(f"{'='*60}\n")

    try:
        syn = Synapse()
        schemas, file_paths = generate_jsonschema(
            data_model_source=data_model_source,
            synapse_client=syn,
            data_types=data_types,
            output=output_dir,
            data_model_labels=data_model_labels
        )

        # Write outputs to GITHUB_OUTPUT
        github_output = os.environ.get('GITHUB_OUTPUT')
        if github_output:
            with open(github_output, 'a') as f:
                f.write(f'schemas={output_dir}\n')
                # Output schemas as JSON for PR comment actions
                schemas_json = json.dumps(schemas)
                # GitHub Actions multiline output format
                f.write('schemas-json<<EOF\n')
                f.write(schemas_json)
                f.write('\nEOF\n')

        # Print success summary
        print(f"::notice::Successfully generated {len(file_paths)} schema(s)")
        for path in file_paths:
            # Get just the filename for cleaner output
            filename = Path(path).name
            print(f"  - {filename}")

        return 0

    except Exception as e:
        print(
            f"::error::Schema generation failed ({type(e).__name__}): {str(e)}",
            file=sys.stderr
        )
        import traceback
        traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
