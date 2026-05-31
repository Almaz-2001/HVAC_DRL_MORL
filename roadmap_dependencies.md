# Roadmap Dependency Table

This file is the single source of truth for which prerequisite sections must
already be complete before a given section in `roadmap.md` can run. It is
referenced from `roadmap.md` Section 0.5 and is intentionally kept as a
separate file so that the main roadmap stays focused on commands while this
file stays focused on structural dependencies.

Read order: a row's "Reads from" column lists the prerequisite sections that
produce the inputs that row's section consumes. A blank "Reads from" cell
means the section is independent of compute closure.

## Compute-producing sections (Block 1, Block 2, Block 3)

| Section | Title                                                    | Reads from                                  | Produces outputs consumed by |
|---------|----------------------------------------------------------|---------------------------------------------|------------------------------|
| 1       | Block 1: v3 Direct-TSup Surrogate                        | --                                          | 2, 3, 4, 5, 6, 8, 9, 15      |
| 2       | Block 1: v3.5 Inverse Calibration                        | 1 (semantic; not strictly required)         | 2.5, 3, 4.5, 5, 5.5, 6, 8, 9, 15 |
| 2.5     | Block 1: Corpus-Matched v3 Retraining (reviewer mitigation) | 1, 2                                     | 3 (reviewer-mitigation row in §5.3) |
| 3       | Block 1: Article-Facing Fidelity Tables and Figures      | 1, 2, 2.5 (optional reviewer-mitigation row) | 11                           |
| 4       | Block 2: Pure v3 Thermostatic Baseline                   | 1                                           | 5.5, 11                      |
| 4.5     | Block 2 Negative Control: Direct v3.5 Warm-Start         | 2                                           | 11                           |
| 5       | Block 2: Thermostatic Hybrid Sweep                       | 1, 2                                        | 5.5, 11, 15                  |
| 5.5     | Block 1.3 / Block 2 Transfer Diagnostics                 | 2, 4, 5                                     | 11                           |
| 6       | Block 2: HDRL Sweep                                      | 1, 2                                        | 11                           |
| 6.5     | MORL 5D Observation Failure (frozen artifact only)       | --                                          | 11                           |
| 7       | Block 2: MORL 17D Power-Only Backend (descriptive)       | --                                          | (preamble to Section 8)      |
| 8       | MORL Pareto Sweep                                        | 1, 2                                        | 11                           |
| 9       | MORL Canonical Seed Analysis                             | 1, 2, 8                                     | 11, 15                       |
| 10      | PI Baseline                                              | --                                          | 11                           |
| 15      | Block 3 Execution: Transferability on Hydronic Family    | 1, 2, 5, 9, 14                              | 16, 17                       |

## Article-build sections

| Section | Title                                                    | Reads from                                  | Produces outputs consumed by |
|---------|----------------------------------------------------------|---------------------------------------------|------------------------------|
| 11      | Rebuild Block 2 Tables and Figures                       | 3, 4, 4.5, 5, 5.5, 6, 6.5, 8, 9, 10         | 12                           |
| 12      | Rebuild the Word Article Skeleton                        | 11                                          | (final manuscript)           |
| 17      | Paper Manuscript Build Path                              | 11, 12, 15                                  | (final manuscript)           |

## Independent sections (no compute closure)

| Section | Title                                                    | Role                                        |
|---------|----------------------------------------------------------|---------------------------------------------|
| 0       | Runtime Checks                                           | Container health / BOPTEST RTE lifecycle    |
| 13      | Audit Anchors                                            | Reference list of pre-registration commits  |
| 13.5    | Pre-Block-3 Cleanup Workflow                             | Repository hygiene before Block 3 opens     |
| 14      | Block 3: Transferability Pre-Registration                | Manifest; must be committed before Section 15 runs |
| 16      | Audit Anchor Chain (Updated)                             | Reference list including Block 3 closure SHA |

## Notes

- **Section 2 reads from Section 1**: technically v3.5 calibration does not
  require the v3 backbone checkpoint to exist, but the two are semantic
  extensions of the same surrogate family and share data conventions; for
  reproduction order we keep Section 2 after Section 1.
- **Section 14 is a manifest, not compute**: it must be committed (and the
  commit SHA recorded as the third audit anchor) before any Section 15 run.
  Otherwise Block 3 cannot claim pre-registered status.
- **Section 6.5 is a frozen artifact**: the 5D MORL failure is preserved as
  a reference CSV in `reports/`; the current 17D code path does not
  regenerate it, so it has no compute prerequisites.
- **Section 15 has two manifest-style prerequisites**: Section 14 (Block 3
  pre-registration), and the Block 2 frozen models referenced in the
  manifest (Sections 5 and 9). All three must be in place before any
  Section 15 cell runs.
- **Independent sections have no compute-closure dependency** but still have
  a temporal ordering inside the roadmap (e.g., audit anchors in Section 13
  presuppose the MORL canonical work of Section 9 has been committed).
