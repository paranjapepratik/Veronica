repo: paranjapepratik/Veronica
branch: main

## Last sync
date: 2026-08-22T00:20:00Z

### Updated in this project
- Veronica v5.0: batch AI scoring (5 papers/call) + small scoring model — roughly 4–6× faster.
- Relevance rewritten: concept coverage dominates, phrase and title hits weighted, local "why it ranked here" on every row.
- Added overview charts, RIS/BibTeX export, first-run intro, Word review export, app icon (.ico/.icns) and PyInstaller build.

## Screen map
| Project screen | Repo files it maps to |
| --- | --- |
| Brief & diagnosis | veronica.py v3 (`pubmed_search`, `_search_impl`, `analyze_paper_ollama`), README.md |
| 1a Instrument panel (light/dark) | veronica.py `Veronica._build`, `_apply_theme`, `_render_detail` |
| 1b Dark instrument | veronica.py `THEMES["dark"]`, `_drain` log pane |
| 1c Screening board | veronica.py `screen`, `cluster_themes`, `open_overview` |
| Excel output | veronica.py `save_workbook` |
| Word review | veronica.py `Docx`, `save_review_docx` |
| Citation export | veronica.py `save_ris`, `save_bibtex` |
| App icon / builds | assets/veronica.ico, assets/veronica.icns, veronica.spec, BUILD.md |

## Sync history
- 2026-08-21T23:40:00Z — v4.0 rewrite: retrieval budget, MeSH query builder, rubric scoring, three sources.
- 2026-08-21T23:05:00Z — first read of `veronica.py` + `README.md`; diagnosis and three UI directions.
