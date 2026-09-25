from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml

ALLOWED_RECORDED_STATUSES = [
    "new",
    "quoted",
    "accepted_unpaid",
    "accepted_paid",
    "in_delivery",
    "completed",
    "cancelled",
    "insufficient_evidence",
]


@dataclass(frozen=True)
class CasePlan:
    scenario_name: str
    difficulty: str
    target_status: str


@dataclass(frozen=True)
class ScenarioConfig:
    seed: int
    total_cases: int
    total_notes_min: int
    total_notes_max: int
    difficulty_note_ranges: dict[str, tuple[int, int]]
    author_roles: dict[str, float]
    note_categories: list[str]
    case_plans: list[CasePlan]


def load_scenario_config(config_path: str) -> ScenarioConfig:
    raw = _load_yaml(config_path)

    difficulty_ranges = {
        key: (int(value[0]), int(value[1]))
        for key, value in _expect_dict(raw, "difficulty_note_ranges").items()
    }
    author_roles = {key: float(value) for key, value in _expect_dict(raw, "author_roles").items()}

    note_categories = [str(item) for item in _expect_list(raw, "note_categories")]
    scenario_packs = _expect_list(raw, "scenario_packs")
    case_plans: list[CasePlan] = []

    for pack in scenario_packs:
        pack_dict = _expect_mapping(pack)
        count = int(pack_dict["count"])
        for _ in range(count):
            case_plans.append(
                CasePlan(
                    scenario_name=str(pack_dict["name"]),
                    difficulty=str(pack_dict["difficulty"]),
                    target_status=str(pack_dict["target_status"]),
                )
            )

    target = _expect_dict(raw, "target")
    config = ScenarioConfig(
        seed=int(raw["seed"]),
        total_cases=int(target["total_cases"]),
        total_notes_min=int(target["total_notes_min"]),
        total_notes_max=int(target["total_notes_max"]),
        difficulty_note_ranges=difficulty_ranges,
        author_roles=author_roles,
        note_categories=note_categories,
        case_plans=case_plans,
    )

    _validate_scenario_config(config)
    return config


def build_seed_payload(
    config: ScenarioConfig, seed_override: int | None = None
) -> dict[str, list[dict[str, Any]]]:
    rng = random.Random(config.seed if seed_override is None else seed_override)

    case_plans = list(config.case_plans)
    rng.shuffle(case_plans)

    service_requests: list[dict[str, Any]] = []
    interaction_notes: list[dict[str, Any]] = []
    quotes: list[dict[str, Any]] = []
    payments: list[dict[str, Any]] = []

    note_counter = 1
    quote_counter = 1
    payment_counter = 1

    base_start = datetime(2026, 1, 1, 8, 0, tzinfo=UTC)

    for index, case_plan in enumerate(case_plans, start=1):
        request_id = f"SR-{index:04d}"
        created_at = base_start + timedelta(days=index * 2 + rng.randint(0, 3))

        recorded_status = _derive_recorded_status(
            case_plan.target_status, case_plan.scenario_name, rng
        )
        service_requests.append(
            {
                "id": request_id,
                "customer_name": f"Synthetic Customer {index:03d}",
                "recorded_status": recorded_status,
                "created_at": created_at,
                "updated_at": created_at,
            }
        )

        note_min, note_max = config.difficulty_note_ranges[case_plan.difficulty]
        note_count = rng.randint(note_min, note_max)
        request_notes = _generate_notes(
            request_id=request_id,
            case_plan=case_plan,
            note_count=note_count,
            created_at=created_at,
            start_counter=note_counter,
            author_roles=config.author_roles,
            note_categories=config.note_categories,
            rng=rng,
        )
        note_counter += len(request_notes)
        interaction_notes.extend(request_notes)

        case_quotes, quote_counter = _generate_quotes_for_case(
            request_id=request_id,
            case_plan=case_plan,
            created_at=created_at,
            next_counter=quote_counter,
            rng=rng,
        )
        quotes.extend(case_quotes)

        case_payments, payment_counter = _generate_payments_for_case(
            request_id=request_id,
            case_plan=case_plan,
            created_at=created_at,
            next_counter=payment_counter,
            rng=rng,
        )
        payments.extend(case_payments)

    payload = {
        "service_requests": service_requests,
        "interaction_notes": interaction_notes,
        "quotes": quotes,
        "payments": payments,
    }
    _validate_payload(payload, config)
    return payload


def _generate_notes(
    request_id: str,
    case_plan: CasePlan,
    note_count: int,
    created_at: datetime,
    start_counter: int,
    author_roles: dict[str, float],
    note_categories: list[str],
    rng: random.Random,
) -> list[dict[str, Any]]:
    notes: list[dict[str, Any]] = []
    current_time = created_at + timedelta(hours=2)

    for local_index in range(note_count):
        note_id = f"NOTE-{start_counter + local_index:06d}"
        current_time += timedelta(hours=rng.randint(4, 36))
        if local_index % 6 == 0:
            current_time += timedelta(days=rng.randint(1, 3))

        category = _choose_note_category(case_plan, note_categories, local_index, note_count, rng)
        author_role = _weighted_choice(author_roles, rng)
        note_text = _build_note_text(case_plan, category, local_index, note_count, rng)

        notes.append(
            {
                "id": note_id,
                "service_request_id": request_id,
                "note_timestamp": current_time,
                "note_category": category,
                "note_text": note_text,
                "author_role": author_role,
            }
        )

    return notes


def _generate_quotes_for_case(
    request_id: str,
    case_plan: CasePlan,
    created_at: datetime,
    next_counter: int,
    rng: random.Random,
) -> tuple[list[dict[str, Any]], int]:
    quote_count = 0
    if case_plan.target_status != "insufficient_evidence":
        quote_count = 1
    if (
        case_plan.scenario_name in {"contradictory_timeline", "long_history_with_reversal"}
        and rng.random() < 0.6
    ):
        quote_count = 2

    rows: list[dict[str, Any]] = []
    for step in range(quote_count):
        quote_id = f"Q-{next_counter:04d}"
        next_counter += 1

        issued_at = created_at + timedelta(days=1 + step * 2, hours=rng.randint(1, 10))
        quote_status = "issued"
        if case_plan.target_status in {
            "accepted_unpaid",
            "accepted_paid",
            "in_delivery",
            "completed",
        }:
            quote_status = "accepted"
        if case_plan.target_status == "cancelled" and step == quote_count - 1:
            quote_status = "withdrawn"

        rows.append(
            {
                "id": quote_id,
                "service_request_id": request_id,
                "quote_timestamp": issued_at,
                "quote_status": quote_status,
                "amount": Decimal(rng.randint(750, 7000)),
            }
        )

    return rows, next_counter


def _generate_payments_for_case(
    request_id: str,
    case_plan: CasePlan,
    created_at: datetime,
    next_counter: int,
    rng: random.Random,
) -> tuple[list[dict[str, Any]], int]:
    target = case_plan.target_status
    payment_count = 0

    if target in {"accepted_paid", "in_delivery", "completed"}:
        payment_count = rng.randint(1, 3)
    if case_plan.scenario_name == "long_history_with_reversal":
        payment_count = rng.randint(2, 4)
    if case_plan.scenario_name == "contradictory_timeline" and rng.random() < 0.5:
        payment_count = rng.randint(1, 2)

    rows: list[dict[str, Any]] = []
    for step in range(payment_count):
        payment_id = f"PAY-{next_counter:04d}"
        next_counter += 1

        paid_at = created_at + timedelta(days=3 + step * 4, hours=rng.randint(2, 12))
        payment_status = "paid"
        if case_plan.target_status == "cancelled" and step == payment_count - 1:
            payment_status = "reversed"

        rows.append(
            {
                "id": payment_id,
                "service_request_id": request_id,
                "payment_timestamp": paid_at,
                "payment_status": payment_status,
                "amount": Decimal(rng.randint(200, 3500)),
            }
        )

    return rows, next_counter


def _derive_recorded_status(target_status: str, scenario_name: str, rng: random.Random) -> str:
    if scenario_name in {"contradictory_timeline", "long_history_with_reversal"}:
        options = [status for status in ALLOWED_RECORDED_STATUSES if status != target_status]
        return rng.choice(options)
    if scenario_name == "sparse_evidence":
        return rng.choice(["new", "quoted", "insufficient_evidence"])
    return target_status


def _choose_note_category(
    case_plan: CasePlan,
    note_categories: list[str],
    local_index: int,
    note_count: int,
    rng: random.Random,
) -> str:
    if case_plan.target_status == "cancelled" and local_index >= note_count - 2:
        return "cancellation_signal"
    if case_plan.target_status == "completed" and local_index >= note_count - 2:
        return "completion_signal"
    if case_plan.target_status == "in_delivery" and local_index >= note_count - 3:
        return "delivery_update"
    if case_plan.scenario_name == "contradictory_timeline" and local_index % 5 == 0:
        return "risk_flag"
    return rng.choice(note_categories)


def _build_note_text(
    case_plan: CasePlan,
    category: str,
    local_index: int,
    note_count: int,
    rng: random.Random,
) -> str:
    status_hint = case_plan.target_status.replace("_", " ")

    templates: dict[str, list[str]] = {
        "customer_contact": [
            "Customer confirmed update call; they requested progress confirmation by end of week.",
            "Customer advised availability window and asked for status to be reconfirmed after internal approval.",
        ],
        "internal_update": [
            "Internal review notes evidence alignment is partial; follow-up required before status can be treated as final.",
            "Case handler logged that chronology is mostly consistent but one earlier note may now be superseded.",
        ],
        "scheduling": [
            "Scheduling team held provisional slot pending customer confirmation and engineering capacity check.",
            "Appointment options shared with customer; awaiting final timeslot acceptance.",
        ],
        "commercial": [
            "Commercial team confirmed quoted amount and noted that acceptance language appears in latest correspondence.",
            "Quote details were clarified; minor scope point remains open and could influence timing.",
        ],
        "payment": [
            "Finance note indicates payment signal captured, but reconciliation entry is pending batch confirmation.",
            "Billing update records partial payment evidence and flags verification for final posting run.",
        ],
        "delivery_update": [
            "Field update indicates work has commenced with no completion confirmation yet logged.",
            "Engineer note reports in-progress execution and a follow-up checkpoint planned.",
        ],
        "completion_signal": [
            "Completion note recorded with customer acknowledgement and no subsequent contradictory update found.",
            "Team lead logged completion evidence and advised closure checks to confirm final status.",
        ],
        "cancellation_signal": [
            "Cancellation request captured and marked as current direction unless superseding instruction arrives.",
            "Case marked withdrawn after customer communication; monitoring for reinstatement signals.",
        ],
        "risk_flag": [
            "Potential contradiction identified: latest narrative differs from earlier operational update and requires review.",
            "Risk note: evidence sequence is ambiguous and may indicate stale recorded status.",
        ],
        "administrative": [
            "Administrative update logged for audit completeness; no decisive status evidence added in this entry.",
            "Routine case housekeeping completed with reference checks and timeline ordering confirmation.",
        ],
    }

    sentence = rng.choice(templates.get(category, templates["administrative"]))
    if local_index in {0, note_count - 1}:
        sentence += f" Current intended lifecycle signal is {status_hint}."
    return sentence


def _validate_payload(payload: dict[str, list[dict[str, Any]]], config: ScenarioConfig) -> None:
    case_count = len(payload["service_requests"])
    note_count = len(payload["interaction_notes"])

    if case_count != config.total_cases:
        raise ValueError(f"Expected {config.total_cases} service requests, got {case_count}")

    if note_count < config.total_notes_min or note_count > config.total_notes_max:
        raise ValueError(
            f"Expected notes in range {config.total_notes_min}-{config.total_notes_max}, got {note_count}"
        )


def _validate_scenario_config(config: ScenarioConfig) -> None:
    if len(config.case_plans) != config.total_cases:
        raise ValueError(
            f"Scenario pack total ({len(config.case_plans)}) does not match target total_cases ({config.total_cases})"
        )

    missing_ranges = {plan.difficulty for plan in config.case_plans} - set(
        config.difficulty_note_ranges
    )
    if missing_ranges:
        raise ValueError(f"Missing note ranges for difficulties: {sorted(missing_ranges)}")


def _weighted_choice(weights: dict[str, float], rng: random.Random) -> str:
    keys = list(weights.keys())
    probs = list(weights.values())
    return rng.choices(keys, weights=probs, k=1)[0]


def _load_yaml(config_path: str) -> dict[str, Any]:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Scenario file not found: {config_path}")

    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle)

    if not isinstance(loaded, dict):
        raise ValueError("Scenario YAML root must be a mapping")

    return loaded


def _expect_dict(raw: dict[str, Any], key: str) -> dict[str, Any]:
    value = raw.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"Expected mapping for key '{key}'")
    return value


def _expect_list(raw: dict[str, Any], key: str) -> list[Any]:
    value = raw.get(key)
    if not isinstance(value, list):
        raise ValueError(f"Expected list for key '{key}'")
    return value


def _expect_mapping(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("Expected mapping item in scenario_packs")
    return value
