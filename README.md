# Veronica 🔬
### AI-powered literature review — local, keyless, free

Veronica searches **PubMed, Europe PMC, arXiv, Crossref and OpenAlex**, ranks the results
locally in seconds, and — only if you ask it to — scores each paper against your research
question with a local **Ollama** model on an auditable rubric. It downloads open-access
PDFs and writes one organised Excel workbook.

Works in any field: the sources it queries and the rubric it scores on both follow the
field of your question.

No API keys. No subscriptions. Nothing leaves your machine except the literature
queries themselves.

---

## What it does

1. Reads the concepts out of your research question and searches up to five databases.
2. Deduplicates, then ranks everything **locally** (seconds, no model) — coverage of your
   concepts dominates, so papers matching every term rise above papers matching one.
3. Optionally scores the top slice with a local model on a field-appropriate rubric,
   0–3 per criterion with a quoted evidence span.
4. You screen with two keys; it writes an Excel workbook, a Word review draft, and
   RIS/BibTeX for Zotero.

## Install

```bash
pip3 install -r requirements.txt
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.1:8b
# Linux only:
sudo apt-get install python3-tk -y

python3 veronica.py
```

---

## How to use it

1. **Research question** — a full question, not keywords. Scoring is measured against it.
   > Which mouse models are used to study mild cognitive impairment in Alzheimer's disease?

2. **Check what it's searching for.** Veronica reads the concepts out of your question
   and shows them as chips under **SEARCHING FOR**:

   > `alzheimer disease +1`  `mild cognitive impairment +2`  `mouse model +3`

   Those are the ideas that must **all** appear in a paper. `+2` means two synonyms are
   searched too (MCI, cognitive dysfunction…). Press **×** on a chip to widen the search,
   **+ add** to narrow it, **re-read question** after editing the question. **show query**
   reveals the exact PubMed string if you want to audit it.

3. **Retrieval budget** — *Retrieve per source* is how wide you cast (200 is sensible);
   *Pre-rank keep* is how many survive the local BM25 rank and get sent to the model
   (40 ≈ a few minutes on an 8B model with 4 threads).

4. **Run review.** Local ranking finishes in seconds and the table fills immediately —
   that alone is a usable, exported shortlist.

5. **Decide whether to spend the model.** A bar offers AI scoring with a time estimate:
   *SCORE TOP 40 (~4 min)* · *SCORE TOP 10 (~1 min)* · *NOT NOW*. Or press `S` on a single
   row to score just that paper in seconds. The **AI SCORING** switch beside
   SEARCHING FOR sets the behaviour — **ASK ME** (default), **AUTOMATIC**, or **OFF** for
   local ranking only. Leave **Fast mode** on for roughly double the speed.

6. **Screen.** Select a row and press `I` to include, `X` to exclude, `U` to clear,
   `J`/`K` to move, `S` to score one paper, `Enter` to open the PDF or DOI. The right pane shows the rubric
   breakdown with the quoted evidence behind each sub-score.

7. **Draft review** turns the *included* papers into a **Word document** next to the
   workbook: findings prose, a hyperlinked table of included papers, an evidence table per
   paper showing the quote behind every sub-score, references, and a reproducible method
   note — with an updatable table of contents.

---

## Fields

The **FIELD** control beside SEARCHING FOR decides which databases are worth querying and
which rubric the scores use. Leave it on *Detect from my question* or pick one:

| Field | Searches | Rubric |
|---|---|---|
| Life & health sciences | PubMed, Europe PMC, OpenAlex | population · intervention · outcome · design |
| Physical sciences & engineering | arXiv, Crossref, OpenAlex | system/material · method · measurement · validation |
| Computing & information | arXiv, Crossref, OpenAlex | problem/task · approach · evaluation · reproducibility |
| Social sciences & humanities | Crossref, OpenAlex | subject/context · framework · evidence · method |
| General / interdisciplinary | all five | topic match · approach · findings · rigour |

## Reading a score

Each paper gets **0–12**: four criteria at 0–3, each with a verbatim quote from the
abstract as justification. The criteria are the ones for your field (above), and the
rubric in play is named in the detail pane and on the workbook's Search sheet.

If a score looks wrong, the quote next to it usually shows why — and that is the point:
a number you can argue with beats a number you can only trust.

---

## Output

```
Desktop/Veronica/2026-08-21/alzheimer disease, mild cognitive impairment, mouse model/
├── 2023_Longitudinal_cognitive_decline_in_3xTg-AD_mice.pdf
├── Review_alzheimer disease…_2026-08-21.xlsx
└── Review_alzheimer disease…_2026-08-21.docx
```

The workbook's **Review** sheet carries the screening decision, total, the four
sub-scores, all four evidence quotes, pre-rank score, citation count and source; the
**Search** sheet records the exact query, so a review is reproducible six months later.

---

## Settings

`Retrieve per source`, `Pre-rank keep`, `Min year`, `Ollama threads` and the model name
are all in the right-hand panel. Any model you have pulled works:

```bash
ollama pull llama3.1:8b     # default, best balance
ollama pull mistral         # 7B
ollama pull llama3.2        # 3B, faster, less RAM
```

Your last query, concepts, budget and theme are remembered in `~/.veronica.json`.

---

## Design

The window sizes itself to your screen and remembers your last question. **F11** (or the
FULL SCREEN button) toggles full screen; drag the dividers to resize the three panes.
Search width, model and sources live under **SETTINGS**.

The interface follows the Industry design system — steel-blue on a light technical
ground, or the original gold-on-black, switchable in the title bar. The design source
lives in `Veronica Redesign.dc.html` (open it in a browser) alongside the diagnosis that
drove this version.

---

## Acknowledgements

[PubMed / NCBI Entrez](https://www.ncbi.nlm.nih.gov/home/develop/api/) ·
[Europe PMC](https://europepmc.org/) · [OpenAlex](https://openalex.org/) ·
[Ollama](https://ollama.com) · [Meta LLaMA 3.1](https://llama.meta.com)

MIT License.

## Charts and exports

- **overview charts** (left rail) — publication-year histogram, citation distribution, and
  an evidence map plotting every paper by year against local relevance, sized by score and
  filled when included. Click a dot to jump to that paper.
- **export citations** — writes `.ris` (Zotero, Mendeley, EndNote) and `.bib` (LaTeX) for
  your included papers, with the Veronica score in the note field.

## Building a double-clickable app

See [BUILD.md](BUILD.md) — `pyinstaller --noconfirm veronica.spec` produces
`Veronica.exe` or `Veronica.app` with the icon bundled.
