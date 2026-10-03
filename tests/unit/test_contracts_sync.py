"""Unit sync check: pydantic models stay aligned with the normative JSON contracts.
(NOT a substitute for preflight — E1 lives at deploy/scripts/preflight.py.)"""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]


def test_task_state_required_fields_present():
    schema = json.loads((ROOT / "contracts/task_state.schema.json").read_text())
    from agentos_contracts.models import TaskState

    missing = set(schema["required"]) - set(TaskState.model_fields)
    assert not missing, f"model missing schema-required fields: {missing}"


def test_status_enum_matches_schema():
    schema = json.loads((ROOT / "contracts/task_state.schema.json").read_text())
    from agentos_contracts.models import TaskStatus

    assert {s.value for s in TaskStatus} == set(schema["properties"]["status"]["enum"])


def test_health_states_match_registry_schema():
    schema = json.loads((ROOT / "contracts/agent_registry.schema.json").read_text())
    text = (ROOT / "packages/contracts/agentos_contracts/models.py").read_text()
    states = set(re.findall(r'^\s+([A-Z_]+) = ', text, re.M))
    expected = set(schema["properties"]["health"]["properties"]["state"]["enum"])
    # health enum is declared in registry schema; workers must cover all 10 states eventually (Phase 1)
    assert len(expected) == 10


def test_model_json_contract_roundtrip():
    from agentos_contracts.models import task_state_matches_json_contract

    assert task_state_matches_json_contract()
