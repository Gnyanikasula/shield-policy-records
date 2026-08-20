# SHIELD Policy Records

A portable, citation-grounded policy representation for AI agent governance, first rendered against Microsoft's Agent Control Specification (ACS).

**Status:** personal open source project, not affiliated with any employer or client.

## What this is

This project takes a small, hand-selected set of regulatory requirements already verified in the [SHIELD](https://github.com/Gnyanikasula/KEP_FALL) knowledge graph (a healthcare-AI regulation Q&A system covering GDPR, the EU AI Act, EU MDR 2017/745, UK MDR 2002, and the DUAA 2025) and expresses each one as a **SHIELD Policy Record** — a short, vendor-neutral document naming the regulation and article it was drafted from, reviewed and signed off by a named human before use.

Each record is then rendered into a real, working policy that a live [Agent Control Specification](https://microsoft.github.io/agent-governance-toolkit/packages/agent-control-specification/) runtime enforces against a demonstration agent's tool calls — intercepting a real tool call, evaluating it against the rendered policy, and returning `allow`, `deny`, `warn`, or `escalate`, with the denial reason naming the exact regulation and article that caused it.

The record format is the durable artefact. ACS is used as the first renderer target because it's the most concretely documented, working governance runtime available — not because it's assumed to be the permanent one.

## What this is not

- Not a new standard for AI agent governance — see [Related Work](#related-work) below.
- Not an autonomous compliance engine and not a legal advice system. No policy record is rendered and deployed without a named human reviewer.
- Not a general-purpose regulation-to-Rego compiler for arbitrary regulations or arbitrary agents.
- Not a replacement, competitor, or fork of Microsoft's Agent Governance Toolkit or ACS.
- Not a regulatory monitoring, alerting, or diffing service.

## Related work

Machine-readable, citation-grounded agent governance is an active area, not a new idea:

- **[Policy Cards](https://arxiv.org/abs/2510.24383)** (Oct 2025) — a machine-readable, deployment-layer standard for operational, regulatory, and ethical constraints on AI agents.
- **[OSCAL for AI governance](https://arxiv.org/abs/2604.13767)** (Apr 2026) — reuses NIST's OSCAL standard as a candidate interchange format for AI governance evidence.
- **XACML** (OASIS) and **Ponder** (2001) — machine-readable, deterministic access-policy languages predating this generation of work by two decades.
- **[MI9](https://arxiv.org/abs/2508.03858)** (2025) — an agent intelligence protocol for runtime governance of agentic AI systems.

This project's field vocabulary (`subject`, `action`, `resource`, `condition`, `decision`, `obligation`) deliberately echoes the XACML and Policy Cards conventions rather than inventing new terminology. The honest claim here is not a new standard — it's a concrete, measured instantiation of the same idea, demonstrated end to end against a real, currently shipping governance runtime.

## Architecture

| Stage | What it is | Where |
|---|---|---|
| 1 | Existing SHIELD knowledge graph & hybrid retrieval (Neo4j + ChromaDB), unchanged | external — [KEP_FALL](https://github.com/Gnyanikasula/KEP_FALL) |
| 2 | Requirement selection from the 55-article gold standard, by a human | `reference-data/gold_standard.json` |
| 3 | SHIELD Policy Record — the durable artefact | `records/*.yaml` |
| 4a | Rego translation of each record | `acs/policy/policy.rego` |
| 4b | ACS manifest binding policies to intervention points | `acs/manifest.yaml` |
| 5 | Demonstration agent (plain Python tools, no governance logic inside) | `acs/tools.py`, `acs/agent.py` |
| 6 | Verdict + evidence, citation drawn from the record at run time | `acs/citations.py`, `acs/neo4j_check.py` |

## Repository structure

```
records/                        6 reviewed SHIELD Policy Records (YAML)
reference-data/                 Verified gold standard + corpus text, copied from KEP_FALL
acs/
  manifest.yaml                 ACS manifest: policies + intervention points
  policy/policy.rego            Compiled Rego rules, one block per record
  tools.py                      Plain Python tool functions, no governance logic
  citations.py                  Loads records/*.yaml, indexes by reason_code
  neo4j_check.py                Live cross-check of deontic_type against Neo4j Aura
  agent.py                      Demonstration agent: 3 scenarios (allow / deny / escalate)
  test_all_records.py           Positive + negative test case per record
  test_neo4j_check.py           Standalone Neo4j cross-check runner
  test_escalate.py              Isolated test of the escalate + approval_resolver path
```

## The 6 policy records

| Record | Regulation & article | Deontic type | Governs |
|---|---|---|---|
| `SHIELD-GDPR-022` | GDPR Art. 22(1) | prohibition | `get_fall_risk` — solely automated decisions |
| `SHIELD-GDPR-009` | GDPR Art. 9(1) | prohibition | `get_patient_record` — special category health data |
| `SHIELD-GDPR-005` | GDPR Art. 5(1)(b) | obligation | `send_patient_data` — purpose limitation |
| `SHIELD-AIACT-ANNEXIII` | EU AI Act Annex III, pt. 5(d) | classification_rule | `external_analytics` — emergency healthcare triage classification |
| `SHIELD-AIACT-026` | EU AI Act Art. 26(2) | obligation | `external_analytics` — human oversight |
| `SHIELD-MDR-002` | EU MDR Art. 2(1) | classification_rule | agent-level — medical device classification |

Each record cites verbatim statutory text traced to a specific gold-standard annotation (`obligation.gold_standard_ref`), not a paraphrase.

## Running this

Requires Python 3.11+, [OPA](https://www.openpolicyagent.org/), and (for the live Neo4j cross-check) a running Neo4j Aura instance.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install agent-control-specification pyyaml neo4j

# OPA (Linux):
curl -sL -o opa https://github.com/open-policy-agent/opa/releases/latest/download/opa_linux_amd64_static
chmod +x opa && sudo mv opa /usr/local/bin/opa
```

For the live Neo4j cross-check, create a `.env` file at the repo root (never committed):

```
NEO4J_URI=neo4j+s://your-instance-id.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j
```

Run the full record test suite:

```bash
cd acs
python3 test_all_records.py
```

Run the demonstration agent (all 3 scenarios — allow, deny, escalate):

```bash
python3 agent.py
```

## Limitations

This project expresses regulatory requirements from a knowledge graph as portable SHIELD Policy Records, and renders them, in this first version, into Microsoft's Agent Control Specification format. It does not issue compliance verdicts and it is not a legal advice system. It is a demonstration, not a proposal, of the machine readable governance policy idea already argued for in Policy Cards, the OSCAL for AI governance literature, and the XACML lineage. The underlying knowledge graph's own measured citation accuracy is 0.845 faithful F1, and its measured accuracy at identifying whether a provision obliges, prohibits, or permits is 0.496, both measured against a gold standard that has not yet had independent legal verification. Because of this, no record produced by this project should be rendered and used to govern a live agent without review and sign off by a qualified person.

## License

Apache 2.0. See `LICENSE`.