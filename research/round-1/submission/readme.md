# Round 1 submission

The submitted report and the team's latest presentation.

- [Report (PDF)](report.pdf): investment policy, allocation, backtest and supplementary analysis (13 pages).
- [Presentation (PDF)](presentation.pdf): the latest shared slide deck (16 slides), synced from Overleaf on 12 November 2026.
- [Report LaTeX source](latex/main.tex): saved report project, including figures and bundled DM Sans fonts.
- [Presentation LaTeX source](presentation/main.tex): the full slide project, charts, fonts and logo. A [source ZIP](Presentation_Source.zip) is also included.
- [Printable speaking notes](speaking_notes.docx): the prompts prepared for slides 13–15.

## Editing the report later

Open `latex/main.tex` in Overleaf with the `fonts/` and `figures/` folders alongside it. Select XeLaTeX as the compiler. Alternatively, from the `latex` directory, run `latexmk -xelatex main.tex` with a suitable TeX installation.

The submitted report is unchanged. Both documents have complete editable source folders; generated build files are omitted. Earlier slide versions remain in Git history. See [Rebuilding the reports and slides](../../documents.md) to build both rounds with one command.

The website serves identical PDF copies from `dist/materials/round-1-report.pdf` and `dist/materials/round-1-presentation.pdf`.
