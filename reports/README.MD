# reports/

Computed evidence and the narrative analysis behind it. `reports/*.csv` and
`reports/*.json` are the audit trail: every number in the manuscript traces to a
file here, which is why they are tracked while `outputs/` is not.

Start here for article-facing navigation:

- [literature_review_alignment_block1_block2.md](literature_review_alignment_block1_block2.md)
  maps the literature review and the Hou-and-Evins protocol onto Block 1 and
  Block 2.
- [hou_evins_compliance_matrix.md](hou_evins_compliance_matrix.md) is the
  methodology compliance matrix.
- [block2_mpc_h5_invalidated.md](block2_mpc_h5_invalidated.md) records the run
  that a defect in our own planner invalidated. It is kept rather than deleted:
  quietly re-running would leave the pre-registration looking untouched when a
  completed run had already been seen.

To rebuild any of this from scratch, follow `roadmap.md` in the repository
root; it is the step-by-step path, and `roadmap_dependencies.md` says which
sections have to have run first.
