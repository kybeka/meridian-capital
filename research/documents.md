# Rebuilding the reports and slides

Both rounds include editable LaTeX, the DM Sans font files, logos and every figure used by the documents. The presentations were downloaded from the shared Overleaf projects on **12 November 2026** and compiled locally. Their latest wording is reflected in the repository and website PDFs. The submitted reports are unchanged.

| Document | Main source | Saved PDF | Pages |
| --- | --- | --- | ---: |
| Round 1 report | [main.tex](round-1/submission/latex/main.tex) | [report.pdf](round-1/submission/report.pdf) | 13 |
| Round 1 presentation | [main.tex](round-1/submission/presentation/main.tex) | [presentation.pdf](round-1/submission/presentation.pdf) | 16 |
| Round 2 report | [main.tex](round-2/submission/latex/main.tex) | [AMC2_Report.pdf](round-2/submission/AMC2_Report.pdf) | 12 |
| Round 2 portfolio description | [portfolio_description.tex](round-2/submission/latex/portfolio_description.tex) | [AMC2_Portfolio_Description.pdf](round-2/submission/AMC2_Portfolio_Description.pdf) | 3 |
| Round 2 presentation | [main.tex](round-2/submission/presentation/main.tex) | [AMC2_Presentation.pdf](round-2/submission/AMC2_Presentation.pdf) | 17 |

## Build all five locally

Use a TeX installation with **XeLaTeX** and **latexmk**. MacTeX is installed on the current Mac; TeX Live also works with the required packages. Python runs the small build helper and needs no extra Python packages.

From the repository root:

```bash
python scripts/build_documents.py
```

The PDFs go into `build/documents/`. To rebuild just one:

```bash
python scripts/build_documents.py round-2-presentation
```

The helper runs enough LaTeX passes to resolve contents, slide counts and references. It reads the saved source folders and writes temporary compiler files outside them. It leaves the saved deliverables and website copies unchanged, so edits can be reviewed before publication. `build/` and temporary LaTeX files are ignored by Git.

The checked-in fonts and figures are sufficient for these document builds; no market-data download or notebook execution is needed. Regenerating the analysis or changing chart inputs is a separate step described in each round's notebook.

## Edit in Overleaf

Upload the full source folder, including its font and figure subfolders, and choose **XeLaTeX**. Each document has a `main.tex` except the separate Round 2 portfolio description. The presentation source ZIPs can also be uploaded directly:

- [Round 1 presentation source](round-1/submission/Presentation_Source.zip)
- [Round 2 presentation source](round-2/submission/AMC2_Presentation_Source.zip)

Shared projects: [Round 1 report](https://www.overleaf.com/project/6acea052fb4be150601f2382), [Round 1 presentation](https://www.overleaf.com/project/6acf74587cbaa56d0ba71183), [Round 2 report](https://www.overleaf.com/project/6ae9ddb29f60dfa97d0803c2), [Round 2 presentation](https://www.overleaf.com/project/6ae9e2672f6ea8c4f0fddc87).

[document-build-verification.json](document-build-verification.json) records the build checks and file hashes. A TeX rebuild can change PDF metadata or small rendering details across TeX versions; the stored report PDFs remain the submission record. Earlier presentation versions remain in Git history.
