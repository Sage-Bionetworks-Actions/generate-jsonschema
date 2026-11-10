# CLAUDE.md

## Project

A Docker container GitHub Action. It wraps
`synapseclient.extensions.curator.generate_jsonschema` to turn a CSV/JSONLD data
model into JSON Schema files for Synapse. It is part of DPE-1554 (automated JSON
Schema management). Its sibling action `register-jsonschema` registers the
generated schemas. ELITE and ADKP data-model repos use this action.

## Stack

- Python and synapseclient (with curator extras), both from the base image
  `ghcr.io/sage-bionetworks/synapsepythonclient:vX.Y.Z`. The `Dockerfile` `FROM`
  tag sets the version. The `ci.yml` `python-version` must match the Python
  version in that image.
- pytest, PyYAML (tests only, from `requirements.txt`)
- super-linter v8 (slim) in CI; markdownlint, yamllint, prettier, ruff, checkov,
  trivy configs at root. black, isort, flake8, pylint and textlint have no
  config in the repository, so they use the super-linter defaults.

## Commands

```bash
SYN_VERSION=$(sed -n 's/^FROM .*synapsepythonclient:v\([^ @]*\).*/\1/p' Dockerfile | head -n1)
pip install "synapseclient[pandas,curator]==${SYN_VERSION}"   # same as CI
pip install -r requirements.txt   # test-only deps (PyYAML, pytest)
python -m pytest test -v
docker build -t generate-jsonschema-action .
docker run --rm -e DATA_MODEL_SOURCE="/test/data_model.csv" -v $(pwd)/test:/test generate-jsonschema-action
```

CI (`.github/workflows/ci.yml`) has 3 jobs: pytest, a Docker build, and a run of
the local action (`uses: ./`) on `test/data_model.csv`.

## Data Models

- **Inputs:** `action.yml` `inputs` → `runs.env` (`DATA_MODEL_SOURCE`,
  `DATA_TYPES`, `DATA_MODEL_LABELS`, `OUTPUT_DIRECTORY`) → `os.environ` in
  `main()`. The script reads only env vars, not CLI args.
- **Input rules in `main()`:** If `DATA_TYPES` is empty or only whitespace, it
  becomes `None` (all types). A source that starts with `http://`/`https://` has
  no file-exists check. An invalid `DATA_MODEL_LABELS` value gives a warning and
  changes to `class_label`. It does not fail.
- **Outputs** go to `$GITHUB_OUTPUT`: `schemas` is an absolute path
  (`os.getcwd()` + `OUTPUT_DIRECTORY`, which is `/github/workspace/...` in the
  container). `schemas-json` is `json.dumps` of the schema list, written as a
  multiline heredoc with the delimiter `EOF`. Users parse `schemas-json` (see
  the `README.md` PR-comment example), so do not change its shape.
- **Test fixture `test/data_model.csv`:** 3 template rows (`IsTemplate=TRUE`:
  Datatype1–3), each with one required property. The tests hardcode the counts
  (`TOTAL_SCHEMAS_IN_TEST_MODEL = 3`, "generated 1/2/3 schema(s)"). If you
  change the fixture, update these counts. The `IsTemplate` column needs
  synapseclient ≥ 4.15.0 (older releases needed a develop image).

## Conventions

- `main()` returns an exit code (0/1) and catches all exceptions. Do not raise
  or call `sys.exit` inside it. The `except Exception` has a
  `# noqa: BLE001 # pylint: disable=broad-exception-caught` comment. If you
  remove it, ruff and pylint fail. `write_github_output()` writes the outputs.
  Keep `main()` at 15 local variables or fewer (pylint `too-many-locals`).
- Use GitHub workflow commands for messages: `::error::` to **stderr**,
  `::warning::` and `::notice::` to **stdout**. The tests check the stream
  (`captured.err` vs `captured.out`) and the exact text, for example:

  ```text
  ::error::Schema generation failed: 'InvalidType' is not a valid datatype in the data model
  ```

- To add or rename an input or output, change all 5 places: `action.yml`
  `inputs`/`outputs`, `action.yml` `runs.env`, the script, the `README.md`
  Inputs/Outputs tables, and the lists in `test/test_action_setup.py`. (Revert
  `8cc401a` restored an `output-directory` input that was lost from `action.yml`
  in a linter fix.)
- `test/test_action_setup.py` does string checks on the source: the script must
  contain `from synapseclient import Synapse`,
  `from synapseclient.extensions.curator import generate_jsonschema`,
  `def main():`, and `if __name__ == "__main__":`. The `README.md` must contain
  `# Generate JSON Schema Action`, `data-model-source`, and `schemas-json`. If
  you refactor imports or rename the title, the tests fail.
- Release tags: `vX.Y.Z` and a floating major tag (`v1`) that moves to each new
  1.x release. The `README.md` examples use `@v1`.

## Constraints

- Keep the `Dockerfile` `FROM` tag as the only place that sets the synapseclient
  version. Do not `pip install` synapseclient (or anything else) in the
  `Dockerfile`. The base image has no pip, and Dependabot changes only the
  `FROM` line. A second pin would silently downgrade the client after each
  Dependabot update.
- Keep the `FROM` line in the form `...synapsepythonclient:vX.Y.Z`. CI gets the
  test version from it with
  `sed -n 's/^FROM .*synapsepythonclient:v\([^ @]*\).*/\1/p'` and fails if the
  result is not exactly `X.Y.Z`.
- Use only release image tags, not `develop-<sha>` tags. Dependabot cannot
  follow develop tags, and because of this the action did not get the
  conditional fixes in 4.12/4.14 (DPE-1851).
- When the base image changes the Python version, update `PYTHON_VERSION` in
  `ci.yml` by hand (Dependabot does not change it). The CI step "Check Python
  version matches base image" fails until the two values are the same. Do not
  write the current Python or synapseclient version in this file. Refer to the
  `Dockerfile` `FROM` tag.
- Pin each action whose owner is not `actions/` to a full commit SHA with a
  `# vX.Y.Z` comment. This is the Sage repository security policy (PR #12).
- Create `Synapse()` with no login. Schema generation does not need auth, and
  the action has no token input (SYNPY-1762).

## Antipatterns — Do NOT

- Do NOT reformat `.github/workflows/*.yml` or `action.yml` with prettier.
  `.prettierignore` excludes them on purpose (PR #8). Use yamllint rules
  (`.yaml-lint.yml`) for these files.
- Do NOT trust `.github/copilot-instructions.md`. It is template text: it refers
  to `entrypoint.sh` and shell conventions, but the action is a Python script.
- Do NOT merge with lint failures. super-linter passes on all files
  (`VALIDATE_ALL_CODEBASE: true`), and each change must keep it clean.

## Linting

- To run the full super-linter locally, use the command in the `README.md`
  "Linting" section. Use the same image version as `linter.yml`.
- super-linter runs both black and ruff format. `.ruff.toml` sets
  `line-length = 88` to match black. Do not remove it. Without it, ruff uses 120
  and the two formatters do not agree.
- black and ruff format wrap a long `assert cond, "msg"` in different ways, and
  no setting fixes this. Keep each `assert` on one line of 88 characters or
  less. Use a local variable or a shorter message.
- Line limits: black and ruff 88, pylint 100, flake8 120, markdownlint MD013 80.
  MD013 does not check tables and code blocks. Prettier (`proseWrap: always`)
  wraps Markdown prose at 80 characters.
- textlint (`terminology` rule) rejects words such as `README`, `repo` and
  `hard-code` in plain text. It does not check code spans, so write `README.md`.
- flake8 reports E402 for the import after `sys.path.insert` in the tests, but
  ruff does not. `.ruff.toml` sets `external = ["E402"]`, so ruff RUF100 does
  not report the `# noqa: E402` as unused. Do not remove the setting or the
  `noqa`.

## Testing

- `test/test_integration.py` calls `main()` for real against the installed
  synapseclient. It does not mock anything. Set inputs with
  `monkeypatch.setenv`/`delenv`. An autouse fixture does `chdir` to `tmp_path`,
  so the output goes there.
- To test a new behavior, add a fixture CSV next to `data_model.csv` (for
  example, for conditionals; the current fixture has none). Do not edit the
  shared fixture, because many tests use its counts.

## Related Systems

- `register-jsonschema` (sibling action): uses the same base image and the same
  rule (one version source).
- Behavior changes in schema output come from synapseclient releases, for
  example SYNPY-1769 (property order). Before you change the image tag, compare
  the output for `test/data_model.csv` from the old and new images.
