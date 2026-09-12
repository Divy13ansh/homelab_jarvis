# Documents — What / Why / How

## What

Tiny helper `scripts/create_document.py` converts markdown research output to `pdf`/`docx`. OpenClaw calls it; no full document service.

## Why

OpenClaw can write markdown, but PDF/DOCX needs conversion. Smallest adapter per hierarchy: skill → helper, not service.

## How

### Interface

```bash
python3 scripts/create_document.py --input /data/documents/research/2026-09-12-foo.md --format pdf
# → /data/documents/research/2026-09-12-foo.pdf

python3 scripts/create_document.py --input report.md --format docx --output /data/documents/report.docx
```

Also `title` arg accepted (compat with `create_document(title, content, format)` interface).

### Output layout

```
/data/documents/
└── research/
    ├── 2026-09-12-local-llms.md
    ├── 2026-09-12-local-llms.pdf
    └── 2026-09-12-local-llms.docx
```

### How it works

- `pdf`: `markdown` → HTML → `weasyprint` (preferred, styled). Fallback `reportlab` if weasyprint missing.
- `docx`: `markdown` → `python-docx` paragraphs/headings (table support via fallback).
- `md`: passthrough.

### Deps baked in Dockerfile

`pandoc`, `wkhtmltopdf` (system), `python-docx`, `weasyprint`, `reportlab`, `markdown`.

### Delivery

```text
report.pdf → OpenClaw message tool → Discord (active channel)
```

Helper never knows destination; OpenClaw session routing does.

### Test

```bash
echo "# Hello" > /tmp/t.md
python3 scripts/create_document.py --input /tmp/t.md --format pdf --output /tmp/t.pdf && ls -lh /tmp/t.pdf
python3 scripts/create_document.py --input /tmp/t.md --format docx --output /tmp/t.docx && ls -lh /tmp/t.docx
```
