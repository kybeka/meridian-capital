# Meridian Capital

Website for Meridian Capital's participation in the Asset Management Challenge 2026 at USI.

## Website

GitHub Pages publishes the `dist` directory automatically when changes are pushed to `main`. Deployment status and the current website address are available under **Actions → Deploy website to GitHub Pages** and **Settings → Pages**.

## Edit the website

- `dist/index.html`: page content, team profiles and document links.
- `dist/styles.css`: responsive layout, DM Sans body typography and navy/gold/ivory theme.
- `dist/app.js`: research tabs, performance tabs and mobile navigation.
- `dist/assets/`: images and downloadable materials.

The site uses plain HTML, CSS and JavaScript. No dependency installation or build step is required. DM Sans loads from Google Fonts.

To preview locally with Node.js:

```sh
node preview.mjs
```

Open http://127.0.0.1:4173. Stop the server with Ctrl+C.

Use relative links for local assets and documents so the site works under the repository's Pages path. Add reports to `dist/documents/` and link to `documents/filename.pdf`.

## Content status

This is an academic simulation, not an investment offering. Team profiles, approved investment policy, holdings and performance observations still need to be supplied. Unpublished materials are labelled accordingly. Keep live challenge results separate from historical backtests, and include dates and sources when adding results.

## Logo

The logo was supplied by the team. The website uses a background-cleaned derivative that preserves its composition but slightly softens parts of the artwork. Replace it with the original transparent export when available. The original supplied image was not modified.
