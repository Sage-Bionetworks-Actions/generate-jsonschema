import pytest
from generate_jsonschema_action import main
from pathlib import Path


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

    monkeypatch.setenv("DATA_MODEL_SOURCE", str(Path(__file__).parent / 'data.model.csv'))
    monkeypatch.setenv("DATA_TYPES", "InvalidType")

    res = main()
    captured = capsys.readouterr()

    assert res == 1, "Main function should return 1 when DATA_MODEL_SOURCE is valid but DATA_TYPES are invalid"
    assert "::error::Schema generation failed: 'InvalidType' is not a valid datatype in the data model" in captured.err


def test_main_with_empty_data_type(capsys, monkeypatch):
    """Test that the main function works with empty DATA_TYPES."""

    monkeypatch.setenv("DATA_MODEL_SOURCE", str(Path(__file__).parent / 'data.model.csv'))
    monkeypatch.setenv("DATA_TYPES", " ")

    res = main()
    captured = capsys.readouterr()

    assert res == 0, "Main function should return 0 when DATA_TYPES is empty"
    assert "::notice::Successfully generated 9 schema(s)" in captured.out


def test_main_with_no_data_types(capsys, monkeypatch):
    """Test that the main function works with no DATA_TYPES."""

    monkeypatch.setenv("DATA_MODEL_SOURCE", str(Path(__file__).parent / 'data.model.csv'))
    monkeypatch.delenv('DATA_TYPES', raising=False)

    res = main()
    captured = capsys.readouterr()

    assert res == 0, "Main function should return 0 when DATA_MODEL_SOURCE is valid"
    assert "::notice::Successfully generated 9 schema(s)" in captured.out


def test_main_with_data_types(capsys, monkeypatch):
    """Test that the main function works with valid DATA_TYPES."""

    monkeypatch.setenv("DATA_MODEL_SOURCE", str(Path(__file__).parent / 'data.model.csv'))
    monkeypatch.setenv("DATA_TYPES", "Patient,JSONSchemaComponent")

    res = main()
    captured = capsys.readouterr()

    assert res == 0, "Main function should return 0 when DATA_MODEL_SOURCE is valid"
    assert "::notice::Successfully generated 2 schema(s)" in captured.out


def test_main_file_not_found(capsys, monkeypatch):
    """Test that main returns error when local data model file does not exist."""

    monkeypatch.setenv("DATA_MODEL_SOURCE", "non_existent_file.csv")

    res = main()
    captured = capsys.readouterr()

    assert res == 1, "Main should return 1 when file not found"
    assert "::error::Data model file not found" in captured.err


def test_main_invalid_labels(capsys, monkeypatch):
    """Test that main warns and defaults when DATA_MODEL_LABELS is invalid."""

    monkeypatch.setenv("DATA_MODEL_SOURCE", str(Path(__file__).parent / 'data.model.csv'))
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
    monkeypatch.setenv("DATA_MODEL_SOURCE", str(Path(__file__).parent / 'data.model.csv'))
    monkeypatch.delenv("DATA_TYPES", raising=False)

    res = main()

    assert res == 0
    assert output_file.exists()
    content = output_file.read_text()
    assert "schemas=" in content
    assert "schemas-json<<EOF" in content
