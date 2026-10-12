# leeeo547.github.io

Personal website of Haoran (Leo) Liu, built on [Academic Pages](https://github.com/academicpages/academicpages.github.io).

## Editing content

All publications, projects, experience and skills live in **`_data/bank.yml`**.
Do not edit `_publications/`, `_portfolio/` or `_pages/cv.md` by hand — they are generated.

```bash
python scripts/gen_from_bank.py --check   # validate
python scripts/gen_from_bank.py           # regenerate + print TBD list
python -m pytest tests -q                 # generator tests
```

Only `visibility: public` items are published. Bullets with `status: TBD` are skipped.

## Local preview

Requires Docker Desktop.

```bash
docker compose up --build   # first time (3–5 min)
docker compose up           # afterwards
```

Open <http://localhost:4000>. Edits reload automatically.

## Deploy

Push to `master`; GitHub Pages builds the site at <https://leeeo547.github.io>.
