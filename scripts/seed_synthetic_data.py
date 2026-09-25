from __future__ import annotations

import argparse
from pathlib import Path

from sqlalchemy import delete
from sqlalchemy.orm import Session

from ai_data_quality_poc.storage.db import build_engine
from ai_data_quality_poc.storage.models import InteractionNote, Payment, Quote, ServiceRequest
from ai_data_quality_poc.storage.seeding import build_seed_payload, load_scenario_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Seed synthetic source data for AI Data Quality PoC"
    )
    parser.add_argument(
        "--config",
        default="data/scenarios/phase3_scenarios.yaml",
        help="Path to scenario YAML file",
    )
    parser.add_argument("--seed", type=int, default=None, help="Optional seed override")
    parser.add_argument(
        "--truncate-first",
        action="store_true",
        help="Truncate source tables before seeding",
    )
    return parser


def truncate_source_tables(session: Session) -> None:
    session.execute(delete(InteractionNote))
    session.execute(delete(Quote))
    session.execute(delete(Payment))
    session.execute(delete(ServiceRequest))


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    config = load_scenario_config(args.config)
    payload = build_seed_payload(config, seed_override=args.seed)

    engine = build_engine()
    with Session(engine) as session:
        if args.truncate_first:
            truncate_source_tables(session)
            session.flush()

        session.execute(ServiceRequest.__table__.insert(), payload["service_requests"])
        session.execute(Quote.__table__.insert(), payload["quotes"])
        session.execute(Payment.__table__.insert(), payload["payments"])
        session.execute(InteractionNote.__table__.insert(), payload["interaction_notes"])
        session.commit()

    config_name = Path(args.config).name
    print(
        "Seed complete:",
        f"config={config_name}",
        f"service_requests={len(payload['service_requests'])}",
        f"interaction_notes={len(payload['interaction_notes'])}",
        f"quotes={len(payload['quotes'])}",
        f"payments={len(payload['payments'])}",
    )


if __name__ == "__main__":
    main()
