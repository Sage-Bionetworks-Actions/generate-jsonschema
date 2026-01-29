#!/usr/bin/env python3
"""GitHub Action to generate JSON schemas from data models using synapseclient."""

import os
import sys
import json
from pathlib import Path
from synapseclient import Synapse
from synapseclient.extensions.curator import generate_jsonschema


def main():
    """Main function to generate JSON schemas from data models."""
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
    data_types_str = os.environ.get('DATA_TYPES', None)
    data_types = (
        [dt.strip() for dt in data_types_str.split(',') if dt.strip()]
        if data_types_str
        else None
    )

    # Validate data_model_labels
    data_model_labels = os.environ.get('DATA_MODEL_LABELS', 'class_label')
    if data_model_labels not in ['class_label', 'display_label']:
        print(
            f"::warning::Invalid data_model_labels '{data_model_labels}', "
            f"using 'class_label'"
        )
        data_model_labels = 'class_label'

    # Create output directory relative to current working directory
    # This ensures it's created in the GitHub workspace where artifacts can be uploaded
    output_dir = os.path.join(os.getcwd(), 'schemas')
    os.makedirs(output_dir, exist_ok=True)

    try:
        # 2. Authenticate to Synapse is not needed for the generate_jsonschema functionality
        syn = Synapse()

        # 3. Generate schemas
        schemas, file_paths = generate_jsonschema(
            data_model_source=data_model_source,
            synapse_client=syn,
            data_types=data_types,
            output=output_dir,
            data_model_labels=data_model_labels
        )

        # 4. Write outputs to GITHUB_OUTPUT
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

        # 5. Print success summary
        print(f"::notice::Successfully generated {len(file_paths)} schema(s)")
        for path in file_paths:
            # Get just the filename for cleaner output
            filename = Path(path).name
            print(f"  - {filename}")

        return 0

    except Exception as e:
        print(f"::error::Schema generation failed: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
