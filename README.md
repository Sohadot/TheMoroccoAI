# TheMoroccoAI.com

Independent intelligence and reference infrastructure for Morocco's AI ecosystem. The site is
**not affiliated with, endorsed by or operated by the Government of Morocco** or any institution it
lists.

The site is static and served by GitHub Pages from the root of `main` (`CNAME` → `themoroccoai.com`).
It has no runtime JavaScript, no third-party requests and no build step at deploy time. Generated
pages are committed.

## What is here

| Path | Purpose |
| --- | --- |
| `index.html` | Homepage: thesis, landscape, vocabulary, editorial doctrine, acquisition. Blocks between `<!--r:…-->` markers are generated. |
| `data/evidence.json` | Evidence registry: one record per sourced claim, with source URL, publication and retrieval dates, verbatim excerpts, classification and verification status. |
| `data/ontology.json` | Ontology: entity types, domains, predicates, entities and typed relationships, each citing evidence. |
| `registry/` | Generated pages: registry index, questions page, all evidence, one page per entity. |
| `tools/registry.py` | Validator for referential integrity and claim-classification rules. |
| `tools/build.py` | Static generator: registry pages, homepage blocks, `sitemap.xml`. |
| `tools/check_site.py` | Site gates: links, anchors, metadata, canonicals, third-party resources, accessibility basics, sitemap, contact path, confidential terms, credentials. |
| `tests/` | `unittest` suite, including negative cases for every gate. |
| `assets/` | Registry stylesheet and self-hosted fonts (SIL OFL 1.1, see `assets/fonts/OFL.txt`). |
| `AUDIT_REPORT.md` | Sprint 01 repository audit and its evidence. |

## Claim classifications

Every record carries exactly one classification: **VERIFIED FACT**, **OFFICIAL TARGET**,
**ANNOUNCED PLAN** or **UNVERIFIED CLAIM**. **INDEPENDENT ANALYSIS** is reserved for relationships
the registry infers from two or more records, and it must carry a note. The validator rejects
forward-looking wording in facts, "achieved" wording in targets and plans, targets without a year,
and relationships classified beyond what their evidence supports.

## Lifecycle, origin and attributes

- **Lifecycle** (projects, models, datasets): `announced`, `in-development`, `pilot`, `operational`,
  `released` (models and datasets only) or `discontinued`. Each value must cite `lifecycle_evidence`
  from the entity's own records. Any stage other than `announced` needs a VERIFIED FACT record whose
  `status_evidence` field explicitly declares that stage. `operational` and `pilot` cannot be
  declared by the actor's own website or press, and `released` only by the technical repository
  itself. A signature, presentation or announcement record declares no status, so it can never
  establish delivery.
- **Project kind** (projects): `ai-application`, `compute-infrastructure`, `institute` or
  `agreement`. Operational infrastructure is not an operational AI application: only
  `ai-application` projects count as sector deployments on the questions page.
- **Origin** (companies): `based-in-morocco` (independent source required),
  `self-described-moroccan`, `foreign-moroccan-subsidiary-reported`,
  `foreign-moroccan-operations-verified` (independent primary source required) or `unresolved`,
  with `origin_evidence`. None of these verifies registration or headquarters.
- **Attributes**: technical or descriptive values (parameters, licence, Rmax…). Each cites one of
  the entity's own records. Self-reported benchmark results are not recorded.
- **Secondary press** (`source_type: secondary_press`) can support only ANNOUNCED PLAN or
  UNVERIFIED CLAIM.

`/registry/questions/` is generated from these fields. It answers which organisations have
documented AI activity, which projects are operational or announced, which models and datasets are
public, which sectors have verified deployments, and which relationships are verified.

## Adding or changing a record

1. Retrieve the original source. Add a record to `data/evidence.json` with the next `MAI-EV-NNNN` id
   and a verbatim excerpt. Leave `publication_date` null rather than guessing it.
2. List the record in the `evidence` array of each entity it documents, and list those entities in
   the record's `related_entities`. Add relationships with the predicates defined in `ontology.json`.
3. Run the checks:

```sh
python3 tools/build.py                 # validate, then regenerate pages
python3 tools/check_site.py --network  # site gates (+ MX lookup for the contact domain)
python3 -m unittest discover -s tests  # full suite
```

CI (`.github/workflows/quality.yml`) runs the same commands on every pull request. Python 3.10+ and
the standard library are all that is needed.

## Transfer notes

The domain, this repository (site, generator, validator, tests), the registry data and the visual
identity are separable and can be transferred. No content or data licence has been declared yet;
that is the owner's decision. The bundled fonts remain under the SIL Open Font License.
