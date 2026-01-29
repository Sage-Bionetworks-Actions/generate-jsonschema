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

    # Debug info to understand container file system
    print(f"::group::Debug Info")
    print(f"Current Working Directory: {os.getcwd()}")
    print(f"User ID: {os.getuid()}")
    print("Listing directory contents:")
    for root, dirs, files in os.walk("."):
        for name in files:
            print(os.path.join(root, name))
    print(f"::endgroup::")

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

        # Verify file can be read and show basic info
        print(f"::group::Data Model File Verification")
        print(f"✓ File found: {data_model_source}")
        print(f"  Absolute path: {data_model_path.absolute()}")
        print(f"  File size: {data_model_path.stat().st_size} bytes")
        print(f"  File is readable: {data_model_path.is_file()}")

        # Show first few lines of the CSV
        try:
            with open(data_model_path, 'r', encoding='utf-8') as f:
                lines = [f.readline() for _ in range(5)]
                print(f"  First 5 lines of CSV:")
                for i, line in enumerate(lines, 1):
                    display_line = line.strip()[:150]
                    if len(line.strip()) > 150:
                        display_line += "..."
                    print(f"    Line {i}: {display_line}")
        except Exception as e:
            print(f"  Warning: Could not read file preview: {e}")

        print(f"::endgroup::")

    # Parse data_types: empty string means all types (None)
    data_types_str = os.environ.get('DATA_TYPES', '')
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
        syn = Synapse(debug=True)

        # 3. Generate schemas
        print(f"::group::Schema Generation Parameters")
        print(f"Generating schemas from {data_model_source}...")
        if data_types:
            print(f"  Data types: {', '.join(data_types)}")
        else:
            print("  Data types: All types in model")
        print(f"  Labels: {data_model_labels}")
        print(f"  Output directory: {output_dir}")
        print(f"::endgroup::")

        print("Calling generate_jsonschema function...")
        schemas, file_paths = generate_jsonschema(
            data_model_source=data_model_source,
            synapse_client=syn,
            data_types=data_types,
            output=output_dir,
            data_model_labels=data_model_labels
        )

        print(f"::group::Schema Generation Results")
        print(f"Schemas returned: {len(schemas)}")
        print(f"File paths returned: {len(file_paths)}")
        if file_paths:
            print("Generated files:")
            for fp in file_paths:
                print(f"  - {fp}")
        else:
            print("No files were generated")
        print(f"::endgroup::")

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
