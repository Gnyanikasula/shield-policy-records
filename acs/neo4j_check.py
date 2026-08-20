"""
Live cross-check against the existing SHIELD Neo4j graph (Phase 4).

Important honesty note, established during design of this module: Neo4j
here stores structured triples (subject/predicate/object, with a "deontic"
property on each relationship) -- it does NOT store the verbatim article
text. citation_text in each Policy Record correctly comes from the corpus
(reference-data/regulatory_chunks.json), not from Neo4j, and stays that
way. What THIS module verifies live is narrower and more honest: that the
deontic classification (obligation / prohibition / classification_rule)
a SHIELD Policy Record was built from still matches what the live graph
currently reports for that article, catching drift if the graph is ever
re-populated. If the graph is unreachable (e.g. Aura free tier paused
after 72h idle, a real documented failure mode in the existing SHIELD
system), this fails soft: it reports "unable to verify" rather than
crashing the demo, mirroring the circuit-breaker pattern the existing
SHIELD codebase already uses for the same reason.

Cypher pattern below is lifted from the existing, working
kep_fall.phase_d_engine.engine._BY_ARTICLE_CYPHER, adapted to fetch just
the deontic value for one article_id.
"""

import os
import pathlib
import yaml
import json

from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError, ServiceUnavailable

REPO_ROOT = pathlib.Path(__file__).parent.parent
GOLD_STANDARD_PATH = REPO_ROOT / "reference-data" / "gold_standard.json"

_ARTICLE_CYPHER = """
    MATCH (s:Concept)-[r:REL {article_id: $article_id}]->(o:Concept)
    RETURN DISTINCT r.deontic AS deontic
"""


def _load_env_file(path: pathlib.Path) -> None:
    """Minimal .env loader -- avoids adding python-dotenv as a dependency
    for four lines of config."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def _kg_article_id_for(gold_standard_ref: str) -> str | None:
    with open(GOLD_STANDARD_PATH) as f:
        gold = json.load(f)
    for annotation in gold["annotations"]:
        if annotation["annotation_id"] == gold_standard_ref:
            return annotation.get("kg_article_id")
    return None


def _expected_deontic_for(gold_standard_ref: str) -> str | None:
    with open(GOLD_STANDARD_PATH) as f:
        gold = json.load(f)
    for annotation in gold["annotations"]:
        if annotation["annotation_id"] == gold_standard_ref:
            return annotation.get("deontic_type")
    return None


class Neo4jCrossCheck:
    def __init__(self):
        _load_env_file(REPO_ROOT / ".env")
        self._uri = os.environ.get("NEO4J_URI")
        self._user = os.environ.get("NEO4J_USER", "neo4j")
        self._password = os.environ.get("NEO4J_PASSWORD", "")
        self._database = os.environ.get("NEO4J_DATABASE", "neo4j")
        self._driver = None

    def _get_driver(self):
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                self._uri, auth=(self._user, self._password)
            )
        return self._driver

    def check_record(self, record: dict) -> str:
        """Returns a short human-readable result string. Never raises --
        fails soft with an explanatory message on any connectivity or
        data issue."""
        gold_standard_ref = record["obligation"]["gold_standard_ref"]

        if not self._uri or not self._password:
            return "SKIPPED (no NEO4J_URI/NEO4J_PASSWORD configured in .env)"

        kg_article_id = _kg_article_id_for(gold_standard_ref)
        if not kg_article_id:
            return f"SKIPPED (no kg_article_id found for {gold_standard_ref})"

        expected_deontic = _expected_deontic_for(gold_standard_ref)

        try:
            driver = self._get_driver()
            records, _, _ = driver.execute_query(
                _ARTICLE_CYPHER,
                article_id=kg_article_id,
                database_=self._database,
            )
        except (ServiceUnavailable, Neo4jError, Exception) as e:
            return f"UNABLE TO VERIFY (live Neo4j unreachable: {type(e).__name__})"

        if not records:
            return f"NO GRAPH DATA for article_id={kg_article_id}"

        live_deontic_values = {r["deontic"] for r in records if r["deontic"]}

        if expected_deontic in live_deontic_values:
            return f"MATCH (live graph confirms deontic={expected_deontic} for {kg_article_id})"
        else:
            return (
                f"MISMATCH (record expects deontic={expected_deontic}, "
                f"live graph reports {live_deontic_values} for {kg_article_id})"
            )

    def close(self):
        if self._driver:
            self._driver.close()