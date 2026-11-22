# Vo Hoang Kim — portfolio

Bilingual (EN/VI) one-page portfolio. Plain HTML, CSS and vanilla JS in `site/`; no build step.

- Preview: `python3 scripts/serve.py` → http://localhost:8000/portfolio/
- Tests: `python3 -m unittest discover -s tests -v`
- Deploy: pushing to `main` runs the tests, then publishes `site/` to GitHub Pages
  (`.github/workflows/pages.yml`).
- Live: https://25520969-netizen.github.io/portfolio/
