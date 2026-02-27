import sys
import os
from pathlib import Path
import pytest

# Add src to path for importing the action script
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from generate_jsonschema_action import main

DATA_MODEL_FILE = "data_model.csv"
DATA_MODEL_PATH = Path(__file__).parent / DATA_MODEL_FILE
TOTAL_SCHEMAS_IN_TEST_MODEL = 3


@pytest.fixture(autouse=True)
def run_in_temp_dir(tmp_path, monkeypatch):
    """Run tests in a temporary directory to clean up generated files."""
    monkeypatch.chdir(tmp_path)


def test_main_no_data_model_source(capsys, monkeypatch):
    """Test that the main function needs DATA_MODEL_SOURCE and returns error when it's missing."""

    monkeypatch.delenv('DATA_MODEL_SOURCE', raising=False)

    res = main()
    captured = capsys.readouterr()

    assert res == 1, "Main function should return 1 when DATA_MODEL_SOURCE is missing"
    assert "::error::DATA_MODEL_SOURCE is required" in captured.err


def test_main_with_invalid_data_type(capsys, monkeypatch):
    """Test that the main function returns error when DATA_TYPES are invalid."""

    monkeypatch.setenv("DATA_MODEL_SOURCE", str(DATA_MODEL_PATH))
    monkeypatch.setenv("DATA_TYPES", "InvalidType")

    res = main()
    captured = capsys.readouterr()

    assert res == 1, "Main function should return 1 when DATA_MODEL_SOURCE is valid but DATA_TYPES are invalid"
    print("#################")
    print(captured.err)
    assert "::error::Schema generation failed" in captured.err
    assert "'InvalidType' is not a valid datatype in the data model." in captured.err


@pytest.mark.parametrize(
    "data_types_env, expected_count",
    [
        (None, TOTAL_SCHEMAS_IN_TEST_MODEL),  # Corresponds to delenv
        (" ", TOTAL_SCHEMAS_IN_TEST_MODEL),
        ("Datatype1", 1),
        ("Datatype1,Datatype2", 2),
    ],
    ids=[
        "no_env_var",
        "whitespace_string",
        "one_type",
        "two_types",
    ]
)
def test_main_data_types(capsys, monkeypatch, data_types_env, expected_count):
    """Test schema generation with various DATA_TYPES inputs."""
    monkeypatch.setenv("DATA_MODEL_SOURCE", str(DATA_MODEL_PATH))
    if data_types_env is None:
        monkeypatch.delenv("DATA_TYPES", raising=False)
    else:
        monkeypatch.setenv("DATA_TYPES", data_types_env)

    res = main()
    captured = capsys.readouterr()

    assert res == 0
    assert f"::notice::Successfully generated {expected_count} schema(s)" in captured.out


def test_main_file_not_found(capsys, monkeypatch):
    """Test that main returns error when local data model file does not exist."""

    monkeypatch.setenv("DATA_MODEL_SOURCE", "non_existent_file.csv")

    res = main()
    captured = capsys.readouterr()

    assert res == 1, "Main should return 1 when file not found"
    assert "::error::Data model file not found" in captured.err


def test_main_invalid_labels(capsys, monkeypatch):
    """Test that main warns and defaults when DATA_MODEL_LABELS is invalid."""

    monkeypatch.setenv("DATA_MODEL_SOURCE", str(DATA_MODEL_PATH))
    monkeypatch.setenv("DATA_MODEL_LABELS", "invalid_label")
    monkeypatch.delenv("DATA_TYPES", raising=False)

    res = main()
    captured = capsys.readouterr()

    assert res == 0
    assert "::warning::Invalid data_model_labels 'invalid_label'" in captured.out


def test_main_github_output(tmp_path, monkeypatch):
    """Test that main writes to GITHUB_OUTPUT correctly."""

    output_file = tmp_path / "github_output.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_file))
    monkeypatch.setenv("DATA_MODEL_SOURCE", str(DATA_MODEL_PATH))
    monkeypatch.delenv("DATA_TYPES", raising=False)

    res = main()

    assert res == 0
    assert output_file.exists()
    content = output_file.read_text()
    assert "schemas=" in content
    assert "schemas-json<<EOF" in content


def test_main_with_output_directory(tmp_path: Path, monkeypatch):
    """Tests main function using a custom output directory."""
    output_dir = "output_dir"
    monkeypatch.setenv("OUTPUT_DIRECTORY", output_dir)
    monkeypatch.setenv("DATA_MODEL_SOURCE", str(DATA_MODEL_PATH))
    monkeypatch.delenv("DATA_TYPES", raising=False)

    res = main()

    assert res == 0
    output_path = tmp_path / output_dir
    assert output_path.exists()
    assert output_path.is_dir()
    # Check if schemas were generated in the custom directory
    assert len(list(output_path.glob("*.json"))) == TOTAL_SCHEMAS_IN_TEST_MODEL
