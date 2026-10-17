The canonical Desktop checkout is meridian-capital. Start with [research/round-1](research/round-1/README.md) for the current Bloomberg code, data and results. Earlier implementations remain in Git history.

# Meridian Capital

Website for Meridian Capital's participation in the Asset Management Challenge 2026 at USI.

## Website

GitHub Pages publishes the `dist` directory automatically when changes are pushed to `main`. Deployment status and the current website address are available under **Actions → Deploy website to GitHub Pages** and **Settings → Pages**.

## Edit the website

- `dist/index.html`: page content, team profiles and document links.
- `dist/styles.css`: responsive layout, DM Sans body typography and navy/gold/ivory theme.
- `dist/app.js`: research tabs, active section tracking and mobile navigation.
- `dist/assets/`: images and downloadable materials.

The site uses plain HTML, CSS and JavaScript. No dependency installation or build step is required. DM Sans loads from Google Fonts.

To preview locally with Node.js:

```sh
node preview.mjs
```

Open http://127.0.0.1:4173. Stop the server with Ctrl+C.

Use relative links for local assets and documents so the site works under the repository's Pages path. Add reports to `dist/documents/` and link to `documents/filename.pdf`.

## Round 1 code

The [Round 1 research folder](research/round-1/README.md) contains an executed Jupyter notebook explaining the data, formulas, optimizer, backtest, independent checks and final positions. A separate notebook contains supplementary studies. Inputs are directly in Data/ and results are regular CSV tables. The website’s research-library entry links to this folder on GitHub; the code does not execute in visitors’ browsers.

## Content status

This is an academic simulation, not an investment offering. Team names and portraits are published. Approved investment policy, holdings and performance observations still need to be supplied. Unpublished materials are labelled accordingly. Keep live challenge results separate from historical backtests, and include dates and sources when adding results.

## Logo

The downloadable `dist/assets/meridian-capital-official.png` restores the approved artwork from commit a21e4a8. Only RGB values of fully transparent pixels were cleared. Every visible pixel and every alpha value was verified unchanged. No regeneration, recolouring or shape changes were applied. This is a 1536 × 1024 transparent raster PNG, intended for light backgrounds, not a vector master. The original supplied image remains unchanged. Navigation and favicon assets are separate.

## Team portraits

The five `dist/assets/team/member-0N-white.png` files are the website portraits, in the same order as the named team cards. The original JPEGs are retained. White-background versions were edited using the built-in image generation tool with this shared prompt: replace only the background with solid white; preserve identity, facial features, expression, hair, skin texture, accessories and clothing; use a centered square headshot with headroom and subtle exposure balancing. AI-assisted background edits can introduce small visual differences from the originals.

## Icon and hero

The transparent `dist/assets/meridian-icon.png` appears beside the navigation wordmark. Its 128px derivative `meridian-favicon.png` is the browser icon. The hero uses a decorative SVG meridian diagram, not financial data.

Icon created with the built-in image editing tool from the official logo. Prompt: Extract only the globe, compass star and orbit rings; remove lettering and surrounding glow; preserve the navy/ivory emblem with cool champagne gold on a transparent square background.

The browser favicon uses `dist/favicon.svg` with an embedded PNG and a tighter viewBox around the globe and compass. This enlarges the central emblem at fixed browser-tab sizes; the navigation retains the full emblem.
