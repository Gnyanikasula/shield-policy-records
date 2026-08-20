"""
Runs the live Neo4j cross-check against all 6 SHIELD Policy Records.
Requires a .env file at the repo root with NEO4J_URI / NEO4J_USER /
NEO4J_PASSWORD / NEO4J_DATABASE for your Aura instance.
"""

import pathlib
import yaml

from neo4j_check import Neo4jCrossCheck

RECORDS_DIR = pathlib.Path(__file__).parent.parent / "records"


def main():
    checker = Neo4jCrossCheck()
    try:
        for path in sorted(RECORDS_DIR.glob("*.yaml")):
            with open(path) as f:
                record = yaml.safe_load(f)
            result = checker.check_record(record)
            print(f"{record['record_id']:28s} -> {result}")
    finally:
        checker.close()


if __name__ == "__main__":
    main()