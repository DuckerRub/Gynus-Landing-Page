# Gynus website

Plain HTML and CSS, served by GitHub Pages from `main` at the repository root. No production build step or JavaScript framework is required.

## Pages and language

- `/`: English homepage.
- `/pt-br/`: Brazilian Portuguese homepage and product guides.
- `/es/`: Spanish homepage.
- Existing `/privacy.html`, `/terms.html`, and `/accountInfo.html` stay at their original URLs. Their bodies and existing language controls are unchanged.

Marketing pages serve their language directly in HTML. The three homepages have reciprocal language alternatives and self-canonicals. English is the `x-default`. Supporting guides currently exist only in Portuguese; their links to other languages explicitly lead to those homepages.

## Protected app links

`404.html` handles `/join-group/<token>` while retaining HTTP 404. `/import-plan/` is a separate, non-indexable app handoff. Do not turn either into a marketing route, change its status for SEO, or add it to the sitemap.

The baseline includes the import handoff and invitation improvements already published at `40b3a0d`. This SEO work preserves `404.html`, `import-plan/index.html`, both `.well-known` files, `CNAME`, and `.nojekyll` byte-for-byte against that baseline. Shared handoff styles are retained. Protected hashes live in `scripts/check-site.py`; update them only for an intentional, separately reviewed app-link change.

## Local checks

```sh
python3 scripts/check-site.py
node scripts/check-deep-links.cjs
python3 scripts/preview.py
```

Preview at `http://127.0.0.1:3456/pt-br/`. The preview server serves the actual custom 404 body with status 404, unlike the default Python file server.

In another terminal:

```sh
python3 scripts/check-site.py --live http://127.0.0.1:3456
```

The checks cover metadata, structured-data JSON, canonical and language URLs, internal links/fragments, sitemap exclusions, protected files, and 95 deterministic app-handoff cases. They do not prove OS-level Universal Links/App Links registration or installed-app opening on physical devices.

## Publishing

Keep the existing GitHub Pages branch/root publishing settings and HTTPS enforcement. Publish the technical foundation first, verify it, then publish the Portuguese content. Following each deployment:

```sh
python3 scripts/check-site.py --live https://gynus.fit
```

Run this from the commit actually deployed: it compares live bodies to local files. Wait for the matching Pages build to complete before checking. If a release causes a regression, revert that release's commit; never restore the obsolete pre-import 404 or association files.

## Content maintenance

Edit the checked-in HTML directly. There is no required generator. Keep titles, descriptions, social tags, visible product facts, and JSON-LD consistent. Update the sitemap when adding or retiring a canonical page. Supply `lastmod` only when backed by a real content-change date; it is intentionally omitted now.

Keep developer and store identities consistent. Do not fabricate rating, review, pricing, or offer schema to satisfy a rich-result validator. Basic `MobileApplication` markup can describe the product without guaranteeing eligibility for a particular rich result.

`assets/social-card.svg` is the editable source for the PNG sharing preview. Screenshots are real frames from the already published `demo.mp4` at 3s, 10s and 25s, exported to 480 × 1038 JPEGs. The combined screenshot size is about 155 KiB. They are lazy-loaded with reserved dimensions; the 34 MB video is not embedded or preloaded. Screenshots show the English app and captions disclose that.

## Search consoles

Google already has a verified domain property, so no redundant verification file is added. Bing supplied an HTML verification token now present in the English homepage; keep it in place. The downloaded XML could not be read through macOS Downloads permissions, so the supported meta-tag method is used instead.

Submit `https://gynus.fit/sitemap.xml` in both consoles. Inspect `/`, `/pt-br/`, and all four Portuguese guides. Request indexing where appropriate after successful publication. Keep invite and import handoffs excluded. Verify any new access or account requirements with the owner.

Launch copy, outreach candidates, and the 30/60/90-day review procedure are in [the launch kit](docs/launch-kit.md). Private console metrics should be retained outside this public repository.
