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

## Content status

This is an academic simulation, not an investment offering. Team names and portraits are published. Approved investment policy, holdings and performance observations still need to be supplied. Unpublished materials are labelled accordingly. Keep live challenge results separate from historical backtests, and include dates and sources when adding results.

## Logo

The logo was supplied by the team. The downloadable version is an AI-assisted cleanup with transparent surroundings and cool champagne gold. The original supplied image was not modified.

### Official website logo

`dist/assets/meridian-capital-official.png` is the downloadable full logo, a transparent 1536 × 1024 PNG intended for light backgrounds. The navigation and favicon use separate icon assets. This is a raster file, not a vector master.

Cleaned with the built-in image editing tool. Prompt: Preserve the globe, compass, rings and exact MERIDIAN CAPITAL wording; remove all surrounding haze and glow, use fully transparent surroundings, crisp edges, navy/ivory and cool desaturated champagne gold. Transparency was checked numerically and by compositing a preview onto a light background.

## Team portraits

The five `dist/assets/team/member-0N-white.png` files are the website portraits, in the same order as the named team cards. The original JPEGs are retained. White-background versions were edited using the built-in image generation tool with this shared prompt: replace only the background with solid white; preserve identity, facial features, expression, hair, skin texture, accessories and clothing; use a centered square headshot with headroom and subtle exposure balancing. AI-assisted background edits can introduce small visual differences from the originals.

## Icon and hero

The transparent `dist/assets/meridian-icon.png` appears beside the navigation wordmark. Its 128px derivative `meridian-favicon.png` is the browser icon. The hero uses a decorative SVG meridian diagram, not financial data.

Icon created with the built-in image editing tool from the official logo. Prompt: Extract only the globe, compass star and orbit rings; remove lettering and surrounding glow; preserve the navy/ivory emblem with cool champagne gold on a transparent square background.

The browser favicon uses `dist/favicon.svg` with an embedded PNG and a tighter viewBox around the globe and compass. This enlarges the central emblem at fixed browser-tab sizes; the navigation retains the full emblem.
