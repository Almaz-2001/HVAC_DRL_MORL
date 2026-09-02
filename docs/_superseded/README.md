# Superseded submission ports

Complete, working ports of this paper to journals that are no longer the target.
They are kept rather than deleted because each one is a finished submission set,
and a later reject sends us back to one of them.

The live target is `docs/ieee_access/`. Its prose is sliced from
`docs/paper_asej/manuscript.tex`, which is in turn built from
`docs/paper_combined/` — both of those stay where they are and are **not**
superseded.

| Directory | Journal | Outcome |
| --- | --- | --- |
| `mdpi_Energies/` | MDPI *Energies* | Returned at technical pre-check as out of scope for an energy journal. Not a quality decision. |
| `mdpi_AI/` | MDPI *AI* | Prepared, not submitted; overtaken by the IEEE Access port. |
| `rineng/` | Elsevier *Results in Engineering* | Desk-rejected on novelty. Holds the journal template plus the cover letter, highlights and declaration-of-interests files prepared for it. |

## Reviving one

Both build scripts were re-pointed when they moved here, so they still slice
from the live sources two directories up:

```bash
python docs/_superseded/mdpi_Energies/build_energies.py
```

What they will **not** carry over is anything added to the paper after the port
was frozen. As of the move that means the sign-inversion result, the
monotonicity-constrained retraining and the MPC baseline: those live in
`paper_asej/manuscript.tex` and reach `mdpi_Energies` on a rebuild, but
`mdpi_AI` slices from `paper_combined/`, which predates them. Check what the
rebuild actually produced before submitting any of these anywhere.
