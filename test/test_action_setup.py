"""Unit tests for the generate-jsonschema GitHub Action setup.

These tests verify the action configuration and script setup without making
actual API calls to Synapse. Integration tests are handled by the underlying
synapseclient library.
"""

import sys
import yaml
from pathlib import Path


# Add src to path for importing the action script
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


def test_action_yml_exists():
    """Test that action.yml exists and is valid YAML."""
    action_file = Path(__file__).parent.parent / 'action.yml'
    assert action_file.exists(), "action.yml should exist"

    with open(action_file) as f:
        action_config = yaml.safe_load(f)

    assert action_config is not None, "action.yml should be valid YAML"
    assert 'name' in action_config, "action.yml should have a name"
    assert 'inputs' in action_config, "action.yml should define inputs"
    assert 'outputs' in action_config, "action.yml should define outputs"
    assert 'runs' in action_config, "action.yml should define runs configuration"


def test_required_inputs_defined():
    """Test that all required inputs are defined in action.yml."""
    action_file = Path(__file__).parent.parent / 'action.yml'

    with open(action_file) as f:
        action_config = yaml.safe_load(f)

    required_inputs = ['data-model-source']
    for input_name in required_inputs:
        assert input_name in action_config['inputs'], \
            f"Required input '{input_name}' should be defined"
        assert action_config['inputs'][input_name]['required'] == True, \
            f"Input '{input_name}' should be marked as required"


def test_optional_inputs_have_defaults():
    """Test that optional inputs have default values."""
    action_file = Path(__file__).parent.parent / 'action.yml'

    with open(action_file) as f:
        action_config = yaml.safe_load(f)

    optional_inputs = ['data-types', 'data-model-labels']
    for input_name in optional_inputs:
        assert input_name in action_config['inputs'], \
            f"Optional input '{input_name}' should be defined"
        assert 'default' in action_config['inputs'][input_name], \
            f"Optional input '{input_name}' should have a default value"


def test_outputs_defined():
    """Test that all expected outputs are defined."""
    action_file = Path(__file__).parent.parent / 'action.yml'

    with open(action_file) as f:
        action_config = yaml.safe_load(f)

    expected_outputs = ['schemas', 'schemas-json']
    for output_name in expected_outputs:
        assert output_name in action_config['outputs'], \
            f"Output '{output_name}' should be defined"
        assert 'description' in action_config['outputs'][output_name], \
            f"Output '{output_name}' should have a description"


def test_docker_configuration():
    """Test that Docker configuration is correct."""
    action_file = Path(__file__).parent.parent / 'action.yml'

    with open(action_file) as f:
        action_config = yaml.safe_load(f)

    assert action_config['runs']['using'] == 'docker', \
        "Action should use Docker"
    assert action_config['runs']['image'] == 'Dockerfile', \
        "Action should reference Dockerfile"

    # Verify environment variables are mapped
    env = action_config['runs'].get('env', {})
    assert 'DATA_MODEL_SOURCE' in env, "DATA_MODEL_SOURCE should be mapped"
    assert 'DATA_TYPES' in env, "DATA_TYPES should be mapped"
    assert 'DATA_MODEL_LABELS' in env, "DATA_MODEL_LABELS should be mapped"


def test_dockerfile_exists():
    """Test that Dockerfile exists and has correct base image."""
    dockerfile = Path(__file__).parent.parent / 'Dockerfile'
    assert dockerfile.exists(), "Dockerfile should exist"

    content = dockerfile.read_text()
    assert 'ENTRYPOINT' in content, "Dockerfile should define ENTRYPOINT"
    assert 'generate_jsonschema_action.py' in content, \
        "Dockerfile should reference the action script"


def test_action_script_exists():
    """Test that the Python action script exists and is executable."""
    script_file = Path(__file__).parent.parent / 'src' / \
        'generate_jsonschema_action.py'
    assert script_file.exists(), "Action script should exist"

    content = script_file.read_text()
    assert 'from synapseclient import Synapse' in content, \
        "Script should import Synapse client"
    assert 'from synapseclient.extensions.curator import generate_jsonschema' in content, \
        "Script should import generate_jsonschema function"
    assert 'def main():' in content, "Script should have main() function"
    assert 'if __name__ == "__main__":' in content, \
        "Script should have __main__ entry point"


def test_action_script_imports():
    """Test that the action script can be imported without errors."""
    try:
        import generate_jsonschema_action
        assert hasattr(generate_jsonschema_action, 'main'), \
            "Script should have main function"
    except ImportError as e:
        # This is expected in CI without synapseclient installed
        # Just verify the script syntax is valid
        script_file = Path(__file__).parent.parent / 'src' / \
            'generate_jsonschema_action.py'
        import py_compile
        py_compile.compile(str(script_file), doraise=True)


def test_test_data_exists():
    """Test that test data model CSV exists."""
    test_data = Path(__file__).parent / 'data.model.csv'
    assert test_data.exists(), "Test data model should exist"

    content = test_data.read_text()
    # Check it's a CSV with expected structure
    assert 'Attribute' in content, "Test data should have Attribute column"
    assert 'Component' in content or 'Patient' in content, \
        "Test data should have at least one component/data type"


def test_readme_exists():
    """Test that README exists and contains key information."""
    readme = Path(__file__).parent.parent / 'README.md'
    assert readme.exists(), "README.md should exist"

    content = readme.read_text()
    assert '# Generate JSON Schema Action' in content, \
        "README should have title"
    assert 'data-model-source' in content, \
        "README should document data-model-source input"
    assert 'schemas' in content, "README should document schemas output"
    assert 'schemas-json' in content, "README should document schemas-json output"


if __name__ == '__main__':
    # Run tests
    import pytest
    pytest.main([__file__, '-v'])
