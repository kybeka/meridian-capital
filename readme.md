The canonical Desktop checkout is meridian-capital. Start with [Round 1](research/round-1/readme.md) or [Round 2 / Checkpoint 2](research/round-2/readme.md) for the notebooks, frozen data, results and final deliverables. Earlier committed versions remain in Git history.

Both rounds' reports and presentations include their complete LaTeX sources, fonts and figures. See [Rebuilding the reports and slides](research/documents.md) for the single build command and Overleaf instructions.

# Meridian Capital

Website for Meridian Capital's participation in the Asset Management Challenge 2026 at USI.

## Website

GitHub Pages publishes the `dist` directory automatically when changes are pushed to `main`. Deployment status and the current website address are available under **Actions → Deploy website to GitHub Pages** and **Settings → Pages**.

## Edit the website

- `dist/index.html`: page content, team profiles and document links.
- `dist/styles.css`: responsive layout, DM Sans body typography and navy/gold/ivory theme.
- `dist/app.js`: research tabs, active section tracking and mobile navigation.
- `dist/assets/`: logos, icons and team portraits.
- `dist/materials/`: the published report, presentation and portfolio-description PDFs.

The site uses plain HTML, CSS and JavaScript. No dependency installation or build step is required. DM Sans loads from Google Fonts.

To preview locally with Node.js:

```sh
node preview.mjs
```

Open http://127.0.0.1:4173. Stop the server with Ctrl+C.

Use relative links for local assets and documents so the site works under the repository's Pages path. Put published PDFs in `dist/materials/` and link to `materials/filename.pdf`. Keep each website PDF identical to its corresponding file under `research/round-1/submission/` or `research/round-2/submission/`.

## Round 1 code

The [Round 1 research folder](research/round-1/readme.md) contains an executed Jupyter notebook explaining the data, formulas, optimizer, backtest, independent checks and final positions. A separate notebook contains supplementary studies. Inputs are in `research/round-1/data/`; tables and charts are in `results/` and `studies/` within the same round folder. The website’s research-library entry links to this folder on GitHub; the code does not execute in visitors’ browsers.

## Round 2 code

The [Checkpoint 2 research folder](research/round-2/readme.md) follows the Round 1 layout. Its main notebook explains the post-loss budget, valuations, alphas, six-stock selection, information ratio, historical tests, risk and zero-fee share quantities. A companion notebook completes the FCFF/FCFE, implied-growth and return-timing checks at unchanged holdings. Saved inputs, results, the Excel model, submitted reports and editable report/slide sources are included. The team also edits the documents in Overleaf. The [post-submission checks](research/round-2/post-submission/readme.md) contain the beta audit and dividend discount models. The analysis keeps the weak historical performance and daily risk findings visible.

## Round 2 website

The published Round 2 page is `round-2.html`, linked from the homepage research library. Preview it at `http://127.0.0.1:4173/round-2.html` when `node preview.mjs` is running.

`dist/round-2.html` summarizes the recorded allocation, valuations, catalyst dates, risk, staggered historical tests, Round 1 attribution and complete holdings. `dist/round-2.js` controls the allocation, valuation and DBC-regime comparisons. The report in `dist/materials/round-2-report.pdf` is the team's latest export (ten content pages, plus cover and contents); `dist/data/round2-publication.json` records its hash and dates.

Rebuild the page with an explicitly chosen report export:

```sh
python scripts/build_round2_page.py --report /absolute/path/to/AMC2_Team_Report.pdf
```

The team approved publication on 8 November 2026. The website report matches [the submitted PDF](research/round-2/submission/AMC2_Report.pdf). Editable LaTeX is stored in the repo and in the shared Overleaf project. The final presentation, editable source and rehearsal notes are in the Round 2 submission folder.

## Content status

This is an academic simulation. Rounds 1 and 2 are published; Round 3 is upcoming. The research uses saved inputs at each round’s cutoff. The homepage tracker updates public-price estimates using the confirmed opening holdings and Round 2 rebalance. Its calculation method and update commands are in the [tracking guide](research/tracking/README.md). Historical backtests remain separate from the challenge tracker.

## Reproducing the work

Open Jupyter from the relevant round folder and select **Restart Kernel and Run All**. See the [Round 1 instructions](research/round-1/readme.md) and [Round 2 instructions](research/round-2/readme.md) for notebook order and Python requirements. On the current Mac, the existing `base` conda environment has the tested packages.

From the repository root, rebuild both reports, both presentations and the portfolio description with:

```sh
python scripts/build_documents.py
```

This needs XeLaTeX and latexmk, available in the current MacTeX installation. Rebuilt PDFs go to `build/documents/`; the saved deliverables and website PDFs are preserved. Full source locations and Overleaf instructions are in the [document guide](research/documents.md).

Verified on **12 November 2026** using fresh copies of tracked files: all four notebooks completed **114 code cells with zero errors**, and all five documents rebuilt with the same text and page counts as the saved PDFs. Notebook checks used fresh kernels, cleared outputs and blocked external data access. Temporary verification copies and superseded external working folders have been removed; `Desktop/meridian-capital` is the working checkout.

## Logo

The downloadable `dist/assets/meridian-capital-official.png` restores the approved artwork from commit a21e4a8. Only RGB values of fully transparent pixels were cleared. Every visible pixel and every alpha value was verified unchanged. No regeneration, recolouring or shape changes were applied. This is a 1536 × 1024 transparent raster PNG, intended for light backgrounds, not a vector master. The original supplied image remains unchanged. Navigation and favicon assets are separate.

## Team portraits

The five `dist/assets/team/member-0N-white.png` files are the website portraits, in the same order as the named team cards. The original JPEGs are retained. White-background versions were edited using the built-in image generation tool with this shared prompt: replace only the background with solid white; preserve identity, facial features, expression, hair, skin texture, accessories and clothing; use a centered square headshot with headroom and subtle exposure balancing. AI-assisted background edits can introduce small visual differences from the originals.

## Icon and hero

The transparent `dist/assets/meridian-icon.png` appears beside the navigation wordmark. Its 128px derivative `dist/assets/meridian-favicon.png` is the browser icon. The hero uses a decorative SVG meridian diagram, not financial data.

Icon created with the built-in image editing tool from the official logo. Prompt: Extract only the globe, compass star and orbit rings; remove lettering and surrounding glow; preserve the navy/ivory emblem with cool champagne gold on a transparent square background.

The browser favicon uses `dist/favicon.svg` with an embedded PNG and a tighter viewBox around the globe and compass. This enlarges the central emblem at fixed browser-tab sizes; the navigation retains the full emblem.
