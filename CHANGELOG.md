# Changelog

## v4.0 — retrieval and scoring rebuilt

### Fixed
- **The retrieval budget was never applied.** `_search_impl` passed `show_n` (10) into
  `pubmed_search(max_results=...)` where `fetch_n` belonged, so "Fetch 200" retrieved 10
  records. Every v3 review was a PubMed top-10. Retrieval and the scored shortlist are now
  two separate numbers ("Retrieve per source", "Pre-rank keep").
- **Papers were dropped silently.** v3 discarded any record without an abstract *or*
  without a PMC/DOI link before you could see it. Records are now kept and flagged
  (`PDF` column shows `✓` saved, `—` link only, `·` nothing); "Keep papers without
  full text" is on by default.
- **Abstracts were truncated at 900 characters** before scoring — often mid-methods.
  Now 3000.

### Added
- **Concept-based query builder.** Concepts (one per line) each expand into a
  `("term"[MeSH Terms] OR term[tiab] OR synonyms…)` group; groups are ANDed. The exact
  query string is shown in the window and written to the workbook's Search sheet.
- **Three sources, all keyless.** PubMed (Entrez), Europe PMC (preprints + open access),
  OpenAlex (citation counts — v3's README noted PubMed doesn't expose these).
  Deduped on DOI → PMID → normalised title, with per-record source provenance.
- **Local BM25 pre-rank.** All retrieved records are ranked locally in milliseconds;
  only the top slice is sent to Ollama. Retrieve wide, spend the model narrowly.
- **Rubric scoring instead of a single 1–10 guess.** Four criteria — population,
  intervention, outcome, design — scored 0–3 each with a verbatim quoted span from the
  abstract as evidence. Total 0–12, `temperature 0`, fixed seed, `format: json`.
  Every number is auditable in the UI and in Excel.
- **Concurrent scoring** via a thread pool (1–8 workers) with `keep_alive: 10m`, so the
  model isn't reloaded between papers.
- **Screening.** Include / exclude per paper (`I` / `X`, `U` to clear, `J`/`K` to move),
  counts in the rail, decision written to the workbook.
- **Theme clustering** from abstract terms, as a filter in the left rail.
- **Drafted findings section.** Optional synthesis over the *included* papers only,
  with bracket citations and a reference list, saved as `Draft_review_<date>.md`.
- **Light and dark themes**, switchable in the title bar; the choice and your last
  query persist in `~/.veronica.json`.
- **One workbook instead of two**, with rubric columns, evidence spans, pre-rank score,
  citation counts and a Search sheet recording the exact query.

### Notes
- Scoring quality depends on the model. `llama3.1:8b` is the sane default; a larger
  local model gives noticeably steadier rubric scores.
- The drafted findings section is a first draft, not a citation-safe manuscript.
  Verify every claim against the sources.

## v4.1 — interface

### Fixed
- The window opened at a fixed 1360×900 and could land larger than the screen. It now
  sizes from your actual resolution (94% × 90%, centred), sets a sane minimum, scales its
  type to the screen, remembers a maximised state, and supports full screen (**F11**,
  `Esc` to leave, or the FULL SCREEN button).
- The three panes are now draggable (`PanedWindow`) and both side panels scroll, so
  nothing can be cut off on a short screen.
- Every crowded fixed-width control moved out of the main window into **SETTINGS**.

### Changed
- **One query field, not two.** The separate "Concepts — one per line" box is gone.
  Veronica derives the search concepts from the research question and shows them as
  editable chips under SEARCHING FOR, with the synonym count per chip. The generated
  PubMed string is now behind **show query** rather than always on screen.
- Empty state explains what to do instead of showing a blank table.
- Screening counts, themes and shortcuts consolidated into the left rail.

## v4.2 — the model is now optional

The point of the tool is saving time, so nothing slow happens without you asking.

- **AI scoring is opt-in per run.** Local BM25 ranking finishes in seconds and the results
  are immediately readable and exported. Then a bar appears above the table:
  *"148 papers ranked locally, ready to read. AI scoring adds a 0–12 rubric with quoted
  evidence — about 4 min for the top 40."* with **SCORE TOP 40**, **SCORE TOP 10** and
  **NOT NOW**. Settings › AI scoring sets the default to Ask (new default), Always or Never.
- **Score one paper on demand** — select a row and press `S` (or SCORE THIS). Seconds,
  and useful for spot-checking the top of the list without committing to a batch.
- **Live ETA while scoring**: `scored 12/40 · ~3 m 20 s left · 21 s/paper`, and the run
  button becomes STOP SCORING so you can bail at any point. Papers already scored keep
  their scores.
- **Fast mode** (on by default): shorter context and answer, roughly twice the speed.
- **PDFs are fetched on demand**, not for the whole shortlist up front — opening a paper
  downloads it then. The bulk download is still available in Settings, now off by default.
- The workbook is written as soon as local ranking finishes, then rewritten if you score.
  A run you abandon still leaves a usable file.

## v4.3 — the scoring switch is visible and honest

- The Ask / Automatic / Off choice moved out of Settings into the main window, beside
  SEARCHING FOR, and is shown as a three-way switch with the current state highlighted.
  The old dropdown read "Ask / Always / Never", where "Always" meant *always score* — easy
  to read as *always ask*, which is why a run could start scoring unasked. The labels are
  now ASK ME / AUTOMATIC / OFF, and old settings files migrate to the same meaning.
- Changing it logs what will happen next, so the state is never a guess.

## v4.4 — every field, not just biomedicine

v4.3 was a biomedical tool wearing a general name: PubMed indexes medicine only, and the
PICO rubric (population / intervention / outcome / design) is meaningless for a paper on
semiconductor fatigue or Victorian print culture.

### Sources
- **arXiv** — physics, maths, CS, quantitative biology and finance, statistics.
- **Crossref** — anything with a DOI, i.e. every discipline including the humanities.
- With PubMed, Europe PMC and OpenAlex that's five sources, all keyless, deduped on
  DOI → PMID → title.
- Each source can be toggled, and **PubMed is now switchable off** — it was always on.

### Field profiles
A **FIELD** control sits next to SEARCHING FOR: *Detect from my question* (default) or an
explicit pick. The field decides two things:

1. **Which databases are worth asking.** Computing searches arXiv + Crossref + OpenAlex;
   life sciences searches PubMed + Europe PMC + OpenAlex; and so on.
2. **The rubric.** Four criteria that mean something in that field, still 0–3 each with a
   quoted evidence span, still totalling 0–12:

| Field | Criteria |
|---|---|
| Life & health sciences | population · intervention · outcome · design |
| Physical sciences & engineering | system/material · method · measurement · validation |
| Computing & information | problem/task · approach · evaluation · reproducibility |
| Social sciences & humanities | subject/context · framework · evidence · method |
| General / interdisciplinary | topic match · approach · findings · rigour |

Detection reads the question's vocabulary; whatever it picks is logged and overridable.
The rubric used is shown in the detail pane and recorded on the workbook's Search sheet,
so a score is always interpretable months later. The Excel columns rename themselves to
the rubric in play.

### Also
- Synonym expansion gained non-biomedical entries (LLM, photovoltaic, qubit, higher
  education, qualitative research…).
- MeSH terms are only meaningful for PubMed; every other source gets plain phrase
  OR-groups.

## v4.5 — fixes

- **"Draft review" said no papers were included when papers were included.** It silently
  required each paper to be AI-scored, so with AI scoring OFF every included paper was
  filtered out. Drafting now works from whatever you have: AI summaries when they exist,
  abstracts when they don't, and it says which it used.
- Drafting checks Ollama first and names the problem, instead of failing quietly.
- The detail pane's four action buttons no longer overflow the panel: OPEN PDF is a full
  width primary, with SCORE / INCLUDE / EXCLUDE on a second row.

## v4.6 — app icon, and the draft is a Word document

### Icon
A proper mark: the steel plate, hairline frame and registration crosses of the app's own
visual language with a set serif V. Shipped as `assets/veronica.ico` (256/128/64/48/32/16,
for the Windows taskbar and the built .exe) and PNGs for macOS/Linux window icons; the app
loads whichever fits the platform.

### Draft review → .docx
The draft was a Markdown file. It is now a real Word document, written with the standard
library (no new dependency), containing:

- a title block with the research question, and a properties table — discipline, rubric,
  sources searched, records retrieved, number scored, included/excluded counts, the exact
  query, the model used;
- an **updatable table of contents** (right-click → Update field);
- the drafted **Findings** prose with bracket citations;
- an **Included papers** table whose titles are live hyperlinks to the DOI or full text,
  with venue, year, citation count and score;
- per paper, its summary and an **evidence table**: each rubric criterion, its 0–3 score,
  and the sentence quoted from the abstract that justifies it;
- a **Screened out** table, hyperlinked **References**, and a **Method** paragraph written
  so the search is reproducible.

Tables have repeating header rows, zebra shading and the app's steel accent; headings are
real Word heading styles, so the document outlines and navigates properly. The preview
window gained **OPEN IN WORD** and **SHOW FOLDER**.

## v5.0 — faster scoring, better relevance

### Scoring speed
- **Batch scoring**: five papers per Ollama call instead of one. The prompt preamble, the
  model warm-up and the HTTP round trip are paid once per group rather than per paper.
  Settings › Papers per call (1/3/5/8); an unusable batch answer falls back to scoring
  those papers singly, so nothing is lost.
- **Separate scoring model**, defaulting to `llama3.2:3b`. Scoring is triage — a 3B model
  is roughly 3× faster than 8B and rarely changes which papers rise. Drafting keeps the
  larger model. If the small one isn't pulled, it falls back and says so.
- Together: roughly **4–6× faster** than v4.5 at the same shortlist size. The ETA is now
  measured per paper as it goes, and the final line reports real elapsed time.

### Relevance
The ranking was plain BM25, which rewards a paper mentioning one concept twenty times. Now:

- **Concept coverage dominates.** Papers matching every one of your terms are scored far
  above papers matching one; below half coverage a paper is demoted (×0.45) but never
  hidden.
- **Exact-phrase and title hits count more** — the phrase in the title is worth much more
  than a stray term in the abstract, and synonyms count toward their concept.
- Citation count and recency are gentle tie-breakers, not drivers.
- **Every row now has a reason**, model or no model: the detail pane's "why it ranked here"
  lists each term, whether it hit the title or the abstract, and what was missing. With
  scoring off the SCORE column shows coverage ticks instead of a dot.

### Also
- **Overview charts** — year histogram, citation distribution, and a clickable evidence map
  (year × relevance, sized by score, filled when included).
- **Citation export** — `.ris` and `.bib` of the included papers, Zotero-ready.
- **First-run introduction** with a live Ollama check that explains what still works
  without it, and a sample question.
- **Real empty and loading states** instead of a blank table.
- **macOS icon** (`assets/veronica.icns`) alongside the Windows `.ico`.
- **`veronica.spec` + BUILD.md** — `pyinstaller --noconfirm veronica.spec` builds
  `Veronica.exe` / `Veronica.app` with the icon, no terminal window, plus release notes on
  Gatekeeper and SmartScreen.
