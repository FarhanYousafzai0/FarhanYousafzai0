# Profile art

This profile uses self-contained SVG files so the animation works inside a
GitHub README without JavaScript. The visual direction was inspired by
[Avi Vashishta's animated profile guide](https://www.avivashishta.com/blog/build-animated-github-profile-readme.html),
while the generators in this repository are an independent implementation for
Farhan's profile.

## Files

- `farhan-ascii.svg` is generated from `source-prepped.png` and reveals the
  portrait one terminal row at a time.
- `wordmark.svg` rasterizes the `FY` monogram into ASCII, layers two offset
  shadows for depth, and applies a gentle CSS rocking animation.
- `contrib-heatmap.svg` is generated from public contribution data and refreshed
  every day by GitHub Actions.

## Regenerate the portrait

The portrait tools are intentionally separate from the daily workflow because
their image-processing dependencies are only needed when the source image
changes. Source photos and prepared raster files stay local and are ignored by
Git; only the generated ASCII SVG is published.

```bash
pip install -r scripts/portrait-requirements.txt
python scripts/prep_photo.py source-photo.jpg
python scripts/make_ascii_svg.py
python scripts/make_wordmark_svg.py --mode rock --out wordmark.svg
```

`prep_photo.py` uses `rembg` when its runtime is available and falls back to
OpenCV GrabCut otherwise.

## Refresh contribution art locally

```bash
pip install -r scripts/requirements.txt
python scripts/fetch_contributions.py
python scripts/render_heatmap_svg.py
```

The contribution endpoint is public, so no personal access token is required.
