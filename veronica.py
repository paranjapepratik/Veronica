"""
Veronica — AI-Powered Literature Review Tool  v3.0
Search Engine : PubMed (free, no key needed)
AI Engine     : Ollama (local, free, offline)

Setup (run once):
    pip3 install requests openpyxl biopython
    curl -fsSL https://ollama.com/install.sh | sh
    ollama pull llama3.1:8b

Run:
    python3 veronica.py
"""

import os, re, sys, json, time, threading, datetime
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from pathlib import Path

import requests
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from Bio import Entrez, Medline

# ── Constants ─────────────────────────────────────────────────────────────────
VERSION       = "3.0"
DESKTOP       = Path.home() / "Desktop"
BASE_DIR      = DESKTOP / "Veronica"
TODAY         = datetime.date.today().strftime("%Y-%m-%d")
OLLAMA_URL    = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "llama3.1:8b"
Entrez.email  = "veronica.tool@research.local"   # required by NCBI (any email works)

# ── Colours ───────────────────────────────────────────────────────────────────
BG       = "#0f0f0f"
BG2      = "#181818"
BG3      = "#222222"
GOLD     = "#c4a96a"
GOLD_DIM = "#7a6540"
FG       = "#e8e4dc"
FG2      = "#999990"
FG3      = "#555550"
GREEN    = "#5aaa5a"
RED      = "#c46a6a"
BLUE     = "#6a8ec4"
BORDER   = "#2a2a2a"

# ═════════════════════════════════════════════════════════════════════════════
#  PubMed helpers
# ═════════════════════════════════════════════════════════════════════════════
def pubmed_search(query: str, max_results: int = 50, year_from: str = None) -> list[dict]:
    """
    Search PubMed and return a list of paper dicts.
    Only returns papers that have a full-text link (PMC open access or DOI).
    """
    # Build query with date filter
    full_query = query
    if year_from:
        full_query += f" AND {year_from}:3000[pdat]"

    # Step 1 — search for IDs (fetch more than needed to allow filtering)
    fetch_n = min(max_results * 4, 200)   # fetch extra since we filter for full-text
    handle  = Entrez.esearch(db="pubmed", term=full_query,
                             retmax=fetch_n, sort="relevance")
    record  = Entrez.read(handle)
    handle.close()
    ids = record.get("IdList", [])
    if not ids:
        return []

    # Step 2 — fetch full records in Medline format
    handle  = Entrez.efetch(db="pubmed", id=",".join(ids),
                            rettype="medline", retmode="text")
    records = list(Medline.parse(handle))
    handle.close()

    papers = []
    for rec in records:
        title    = rec.get("TI", "")
        abstract = rec.get("AB", "")
        pmid     = rec.get("PMID", "")
        authors  = rec.get("AU", [])
        journal  = rec.get("TA", "") or rec.get("JT", "")
        year     = ""
        dp       = rec.get("DP", "")
        if dp:
            year = dp.split()[0]
        doi      = ""
        for aid in rec.get("AID", []):
            if "[doi]" in aid:
                doi = aid.replace(" [doi]", "").strip()

        # Build full-text URL: prefer PMC, fall back to DOI
        pmc      = rec.get("PMC", "")
        if pmc:
            fulltext_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc}/pdf/"
            has_fulltext = True
        elif doi:
            fulltext_url = f"https://doi.org/{doi}"
            has_fulltext = True          # DOI present — likely accessible
        else:
            fulltext_url = ""
            has_fulltext = False

        # Skip papers with no abstract or no full-text link
        if not abstract or not has_fulltext:
            continue

        pub_types = rec.get("PT", [])

        papers.append({
            "pmid":         pmid,
            "title":        title,
            "abstract":     abstract,
            "authors":      authors,
            "journal":      journal,
            "year":         year,
            "doi":          doi,
            "pmc":          pmc,
            "fulltext_url": fulltext_url,
            "pub_types":    pub_types,
            "cited_by":     "",          # PubMed doesn't expose citation counts freely
        })

        if len(papers) >= max_results:
            break

    return papers


def download_pdf(paper: dict, folder: Path, log_fn=print) -> str:
    """Try to download the full-text PDF. PMC papers are most reliable."""
    pmc = paper.get("pmc", "")
    doi = paper.get("doi", "")
    title = sanitize(paper.get("title", "untitled"))
    year  = paper.get("year", "")
    dest  = folder / f"{year}_{title}.pdf"

    if dest.exists():
        log_fn(f"  ✓ Already saved: {dest.name}")
        return str(dest)

    # PMC direct PDF download (most reliable)
    urls_to_try = []
    if pmc:
        urls_to_try.append(f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc}/pdf/")
    if doi:
        # Try unpaywall-style open access
        urls_to_try.append(f"https://europepmc.org/articles/{pmc}/pdf/render" if pmc else "")
    urls_to_try = [u for u in urls_to_try if u]

    for url in urls_to_try:
        try:
            r = requests.get(url, timeout=40, stream=True,
                             headers={"User-Agent": "Veronica/3.0 (research tool; mailto:research@local)"})
            ct = r.headers.get("content-type", "")
            if r.status_code == 200 and ("pdf" in ct or "octet" in ct):
                with open(dest, "wb") as f:
                    for chunk in r.iter_content(8192):
                        f.write(chunk)
                kb = dest.stat().st_size // 1024
                if kb > 10:   # ignore tiny error pages saved as PDF
                    log_fn(f"  ✓ Downloaded ({kb} KB): {dest.name}")
                    return str(dest)
                else:
                    dest.unlink(missing_ok=True)
        except Exception as e:
            log_fn(f"  ✗ {url[:60]} → {e}")

    log_fn(f"  ✗ Full PDF not downloadable: {title[:50]}")
    return ""


# ═════════════════════════════════════════════════════════════════════════════
#  Ollama helpers
# ═════════════════════════════════════════════════════════════════════════════
def check_ollama(model=DEFAULT_MODEL):
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=5)
        if r.status_code == 200:
            models = [m["name"] for m in r.json().get("models", [])]
            base   = model.split(":")[0]
            avail  = [m for m in models if base in m]
            if avail:
                return True, avail[0]
            return False, f"Model '{model}' not found. Run: ollama pull {model}"
        return False, "Ollama returned an error."
    except requests.exceptions.ConnectionError:
        return False, "Ollama not running. Start with: ollama serve"
    except Exception as e:
        return False, str(e)


def analyze_paper_ollama(paper: dict, research_q: str, model: str, log_fn=print) -> dict:
    title    = paper.get("title", "")
    abstract = (paper.get("abstract") or "")[:900]
    prompt = (
        f'You are a research assistant doing a systematic literature review.\n\n'
        f'Research question: "{research_q}"\n\n'
        f'Paper title: {title}\n'
        f'Abstract: {abstract}\n\n'
        f'Respond ONLY with a JSON object. No markdown, no explanation. Fields:\n'
        f'- "score": integer 1-10 (relevance to the research question; 10=directly answers it)\n'
        f'- "paper_type": one of "Research Paper","Literature Review","Methods Paper",'
        f'"Case Study","Meta-Analysis","Clinical Trial","Other"\n'
        f'- "summary": 2-3 plain-English sentences: what it investigates, method, main finding\n'
        f'- "reason": 1 sentence explaining the score\n\n'
        f'JSON only:'
    )
    try:
        r = requests.post(OLLAMA_URL, json={
            "model":   model,
            "prompt":  prompt,
            "stream":  False,
            "options": {"temperature": 0.1, "num_predict": 500}
        }, timeout=180)
        raw   = r.json().get("response", "").strip()
        match = re.search(r'\{[\s\S]*?\}', raw)
        if match:
            return json.loads(match.group())
        return {}
    except Exception as e:
        log_fn(f"  Ollama error: {e}")
        return {}


# ═════════════════════════════════════════════════════════════════════════════
#  Excel helpers
# ═════════════════════════════════════════════════════════════════════════════
def sanitize(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*\n\r]', '_', str(name)).strip()[:60]

def make_folder(topic: str) -> Path:
    folder = BASE_DIR / TODAY / sanitize(topic)
    folder.mkdir(parents=True, exist_ok=True)
    return folder

HDR_FONT  = Font(bold=True, color="FFFFFF", size=10, name="Arial")
HDR_FILL  = PatternFill("solid", start_color="1a1a2e")
HDR_ALIGN = Alignment(horizontal="center", vertical="center", wrap_text=True)
THIN      = Side(style="thin", color="cccccc")
CELL_BRD  = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

def _hdr(ws, ncols, row=1):
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.font, cell.fill, cell.alignment = HDR_FONT, HDR_FILL, HDR_ALIGN
    ws.row_dimensions[row].height = 26

def _data(ws, row, ncols, even=False):
    bg = "f4f6ff" if even else "ffffff"
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.font      = Font(name="Arial", size=9)
        cell.fill      = PatternFill("solid", start_color=bg)
        cell.alignment = Alignment(vertical="top", wrap_text=True)
        cell.border    = CELL_BRD

def _link(cell, url, text=None):
    if url:
        cell.hyperlink = url
        cell.value     = text or url
        cell.font      = Font(color="0055cc", underline="single", name="Arial", size=9)

def fmt_authors(authors, max_n=5):
    if not authors: return ""
    names = list(authors)
    return ", ".join(names[:max_n]) + (" et al." if len(names) > max_n else "")

def fmt_types(pub_types):
    keep = ["Journal Article","Review","Clinical Trial","Meta-Analysis",
            "Systematic Review","Case Reports","Letter","Comment"]
    t = [x for x in (pub_types or []) if x in keep]
    return ", ".join(t) if t else "Research Paper"


def save_papers_xlsx(papers, folder, topic, pdf_paths):
    wb = Workbook(); ws = wb.active; ws.title = "Papers"
    cols   = ["#","Title","Authors","Year","Journal","DOI","PMID",
              "Type","PDF Downloaded","Full Text URL"]
    widths = [4, 52, 35, 6, 32, 38, 12, 24, 16, 48]
    for i,(h,w) in enumerate(zip(cols,widths),1):
        ws.cell(1,i,h)
        ws.column_dimensions[get_column_letter(i)].width = w
    _hdr(ws, len(cols))
    for idx,p in enumerate(papers,1):
        doi = p.get("doi",""); pmid = p.get("pmid","")
        pdf = pdf_paths.get(pmid,"")
        row = [idx, p.get("title",""), fmt_authors(p.get("authors",[])),
               p.get("year",""), p.get("journal",""), doi, pmid,
               fmt_types(p.get("pub_types",[])),
               "Yes" if pdf else "No", p.get("fulltext_url","")]
        for c,v in enumerate(row,1): ws.cell(idx+1,c,v)
        ws.row_dimensions[idx+1].height = 38
        _data(ws, idx+1, len(cols), even=(idx%2==0))
        if doi:  _link(ws.cell(idx+1,6), f"https://doi.org/{doi}", doi)
        if pmid: _link(ws.cell(idx+1,7), f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/", pmid)
    # Info sheet
    ws2 = wb.create_sheet("Search Info")
    ws2.column_dimensions["A"].width = 22
    ws2.column_dimensions["B"].width = 65
    for r,(k,v) in enumerate([
        ("Topic", topic), ("Date", TODAY),
        ("Papers found", len(papers)),
        ("PDFs downloaded", sum(1 for v in pdf_paths.values() if v)),
        ("Folder", str(folder)),
        ("Search Engine", "PubMed (NCBI)"),
        ("AI Engine", f"Ollama · {DEFAULT_MODEL}")], 1):
        ws2.cell(r,1,k).font = Font(bold=True,name="Arial",size=10)
        ws2.cell(r,2,str(v)).font = Font(name="Arial",size=10)
    path = folder / f"Papers_{sanitize(topic)}_{TODAY}.xlsx"
    wb.save(path); return path


def save_summaries_xlsx(papers, summaries, folder, topic):
    wb = Workbook(); ws = wb.active; ws.title = "AI Summaries"
    cols   = ["#","Title","Authors","Year","Journal","DOI","PMID",
              "Score","Type","AI Summary","Relevance Reason"]
    widths = [4, 46, 35, 6, 30, 36, 12, 8, 22, 65, 42]
    for i,(h,w) in enumerate(zip(cols,widths),1):
        ws.cell(1,i,h)
        ws.column_dimensions[get_column_letter(i)].width = w
    _hdr(ws, len(cols))
    score_fills = {
        "high":   PatternFill("solid", start_color="c8f0c8"),
        "medium": PatternFill("solid", start_color="ffeaa0"),
        "low":    PatternFill("solid", start_color="ffd0d0"),
    }
    for idx,p in enumerate(papers,1):
        pmid  = p.get("pmid",str(idx))
        s     = summaries.get(pmid, {})
        doi   = p.get("doi","")
        score = s.get("score","")
        row   = [idx, p.get("title",""), fmt_authors(p.get("authors",[])),
                 p.get("year",""), p.get("journal",""), doi, pmid,
                 score, s.get("paper_type", fmt_types(p.get("pub_types",[]))),
                 s.get("summary",""), s.get("reason","")]
        for c,v in enumerate(row,1): ws.cell(idx+1,c,v)
        ws.row_dimensions[idx+1].height = 75
        _data(ws, idx+1, len(cols), even=(idx%2==0))
        if doi:  _link(ws.cell(idx+1,6), f"https://doi.org/{doi}", doi)
        if pmid: _link(ws.cell(idx+1,7), f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/", pmid)
        if isinstance(score, int):
            tier = "high" if score>=7 else "medium" if score>=4 else "low"
            sc = ws.cell(idx+1,8)
            sc.fill = score_fills[tier]
            sc.font = Font(bold=True, name="Arial", size=10)
            sc.alignment = Alignment(horizontal="center", vertical="top")
    path = folder / f"Summaries_{sanitize(topic)}_{TODAY}.xlsx"
    wb.save(path); return path


# ═════════════════════════════════════════════════════════════════════════════
#  GUI
# ═════════════════════════════════════════════════════════════════════════════
class VeronicaApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"Veronica  ·  AI Literature Review  v{VERSION}")
        self.configure(bg=BG)
        self.geometry("1060x820")
        self.minsize(860, 660)
        self._papers    = []
        self._summaries = {}
        self._pdf_paths = {}
        self._folder    = None
        self._running   = False
        self._build_ui()
        self.after(600, self._check_ollama_status)
        self._log(f"Veronica v{VERSION}  —  PubMed + Ollama  |  100% Free", "gold")
        self._log(f"Output folder: {BASE_DIR}")
        self._log("─" * 70)

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        top = tk.Frame(self, bg=BG, pady=12, padx=20); top.pack(fill="x")
        tk.Label(top, text="Veronica", font=("Georgia",22,"bold"),
                 fg=GOLD, bg=BG).pack(side="left")
        tk.Label(top, text="  AI Literature Review", font=("Georgia",13),
                 fg=FG2, bg=BG).pack(side="left", pady=4)
        self.lbl_ollama = tk.Label(top, text="● Checking Ollama…",
                                    font=("Courier",9), fg=FG3, bg=BG)
        self.lbl_ollama.pack(side="right", padx=4)
        tk.Label(top, text=f"v{VERSION} · PubMed · Ollama · Free",
                 font=("Courier",8), fg=FG3, bg=BG).pack(side="right", padx=10)
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        paned = tk.PanedWindow(self, orient="horizontal", bg=BG,
                               sashwidth=4, sashrelief="flat")
        paned.pack(fill="both", expand=True)
        left  = tk.Frame(paned, bg=BG2, padx=18, pady=14)
        right = tk.Frame(paned, bg=BG)
        paned.add(left,  minsize=350, width=390)
        paned.add(right, minsize=440)
        self._build_controls(left)
        self._build_right(right)

    def _sec(self, p, t):
        tk.Label(p, text=t, font=("Courier",8), fg=FG3,
                 bg=BG2).pack(anchor="w", pady=(13,2))

    def _lbl(self, p, t):
        tk.Label(p, text=t, font=("Courier",8), fg=FG3,
                 bg=BG2).pack(anchor="w", pady=(8,2))

    def _entry(self, p, var=None, show=None, font=("Georgia",10)):
        kw = dict(bg=BG3, fg=FG, insertbackground=GOLD, relief="flat", bd=0,
                  font=font, highlightthickness=1,
                  highlightbackground=BORDER, highlightcolor=GOLD)
        if var:  kw["textvariable"] = var
        if show: kw["show"] = show
        e = tk.Entry(p, **kw); e.pack(fill="x", ipady=5); return e

    def _build_controls(self, p):
        # Search
        self._sec(p, "── SEARCH  (PubMed) ────────────────────")
        self._lbl(p, "Keywords / Topic")
        self.v_query = tk.StringVar(); self._entry(p, self.v_query)

        self._lbl(p, "Research Question  (Ollama scores relevance against this)")
        self.txt_rq = tk.Text(p, height=4, bg=BG3, fg=FG, insertbackground=GOLD,
                               relief="flat", bd=0, font=("Georgia",10),
                               highlightthickness=1, highlightbackground=BORDER,
                               highlightcolor=GOLD, wrap="word")
        self.txt_rq.pack(fill="x")

        # PubMed filters
        self._sec(p, "── FILTERS ─────────────────────────────")
        frow = tk.Frame(p, bg=BG2); frow.pack(fill="x", pady=(0,4))
        self.v_year  = tk.StringVar(value="")
        self.v_fetch = tk.StringVar(value="50")
        self.v_show  = tk.StringVar(value="10")
        for col,(ltext,var,vals) in enumerate([
            ("Min Year",    self.v_year,  None),
            ("Fetch Limit", self.v_fetch, ["25","50","100","200"]),
            ("Show Top",    self.v_show,  ["5","10","15","20","25"]),
        ]):
            tk.Label(frow,text=ltext,font=("Courier",8),
                     fg=FG3,bg=BG2).grid(row=0,column=col,sticky="w",padx=(0,10))
            if vals:
                ttk.Combobox(frow,textvariable=var,width=7,
                             values=vals,state="readonly").grid(
                             row=1,column=col,sticky="w",padx=(0,10))
            else:
                tk.Entry(frow,textvariable=var,width=7,bg=BG3,fg=FG,
                         insertbackground=GOLD,relief="flat",bd=0,
                         font=("Georgia",10),highlightthickness=1,
                         highlightbackground=BORDER,highlightcolor=GOLD).grid(
                         row=1,column=col,sticky="w",padx=(0,10),ipady=4)

        # PubMed article type filter
        self._lbl(p, "Article Type Filter  (optional, e.g.: Review, Clinical Trial)")
        self.v_arttype = tk.StringVar(value="")
        self._entry(p, self.v_arttype, font=("Courier",10))
        tk.Label(p, text='Leave blank for all types. PubMed values: "Review" "Clinical Trial" "Meta-Analysis"',
                 font=("Courier",7), fg=FG3, bg=BG2,
                 wraplength=330, justify="left").pack(anchor="w", pady=(2,0))

        # Ollama
        self._sec(p, "── OLLAMA MODEL ────────────────────────")
        self.v_model = tk.StringVar(value=DEFAULT_MODEL)
        mrow = tk.Frame(p, bg=BG2); mrow.pack(fill="x")
        tk.Entry(mrow, textvariable=self.v_model, bg=BG3, fg=FG,
                 insertbackground=GOLD, relief="flat", bd=0, font=("Courier",10),
                 highlightthickness=1, highlightbackground=BORDER,
                 highlightcolor=GOLD).pack(side="left",fill="x",expand=True,ipady=5)
        tk.Button(mrow, text="Check", command=self._check_ollama_status,
                  bg=BG3, fg=FG2, relief="flat", font=("Courier",8),
                  cursor="hand2", padx=8, pady=5).pack(side="right", padx=(6,0))
        tk.Label(p, text="Run:  ollama pull llama3.1:8b  to download the model",
                 font=("Courier",7), fg=FG3, bg=BG2,
                 wraplength=330, justify="left").pack(anchor="w", pady=(3,0))

        # Options
        self._sec(p, "── OPTIONS ─────────────────────────────")
        self.v_download = tk.BooleanVar(value=True)
        self.v_ai       = tk.BooleanVar(value=True)
        self.v_excel    = tk.BooleanVar(value=True)
        self.v_summary  = tk.BooleanVar(value=True)
        for var,text in [
            (self.v_download, "Download full-text PDFs  (PMC open access)"),
            (self.v_ai,       "AI analysis  (Ollama scoring & summaries)"),
            (self.v_excel,    "Save Papers Excel file"),
            (self.v_summary,  "Save AI Summaries Excel file"),
        ]:
            tk.Checkbutton(p, variable=var, text=text, font=("Courier",9),
                           fg=FG2, bg=BG2, selectcolor=BG3,
                           activeforeground=GOLD,
                           activebackground=BG2).pack(anchor="w", pady=1)

        # Buttons
        tk.Frame(p, bg=BORDER, height=1).pack(fill="x", pady=12)
        self.btn_search = tk.Button(p, text="  Search & Analyze  ",
                                     command=self._start_search,
                                     bg=GOLD, fg="#0e0e0e", relief="flat",
                                     font=("Courier",11,"bold"),
                                     activebackground="#d4b87a",
                                     cursor="hand2", pady=10)
        self.btn_search.pack(fill="x")
        self.btn_open = tk.Button(p, text="Open Output Folder",
                                   command=self._open_folder,
                                   bg=BG3, fg=FG2, relief="flat",
                                   font=("Courier",9),
                                   activebackground=BORDER,
                                   cursor="hand2", pady=6)
        self.btn_open.pack(fill="x", pady=(6,0))
        self.btn_stop = tk.Button(p, text="Stop",
                                   command=self._stop,
                                   bg=BG3, fg=RED, relief="flat",
                                   font=("Courier",9),
                                   activebackground=BORDER,
                                   cursor="hand2", pady=6, state="disabled")
        self.btn_stop.pack(fill="x", pady=(4,0))

    def _build_right(self, parent):
        self.progress = ttk.Progressbar(parent, mode="determinate", maximum=100)
        self.progress.pack(fill="x")
        style = ttk.Style(); style.theme_use("default")
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=BG2, foreground=FG2,
                        padding=[14,6], font=("Courier",9))
        style.map("TNotebook.Tab",
                  background=[("selected",BG3)], foreground=[("selected",GOLD)])
        nb = ttk.Notebook(parent); nb.pack(fill="both", expand=True)
        rf = tk.Frame(nb, bg=BG); nb.add(rf, text="  Results  ")
        lf = tk.Frame(nb, bg=BG); nb.add(lf, text="  Log  ")
        self._build_results_tab(rf)
        self._build_log_tab(lf)

    def _build_results_tab(self, parent):
        bar = tk.Frame(parent, bg=BG2, padx=12, pady=8); bar.pack(fill="x")
        self.lbl_count = tk.Label(bar, text="No results yet",
                                   font=("Courier",9), fg=FG3, bg=BG2)
        self.lbl_count.pack(side="left")
        tk.Label(bar, text="Sort:", font=("Courier",9),
                 fg=FG3, bg=BG2).pack(side="right", padx=(0,4))
        self.v_sort = tk.StringVar(value="Relevance")
        ttk.Combobox(bar, textvariable=self.v_sort, width=14,
                     values=["Relevance","Year (newest)","Year (oldest)"],
                     state="readonly",
                     font=("Courier",9)).pack(side="right")
        self.v_sort.trace_add("write", lambda *a: self._render_results())

        cols = ("score","title","year","authors","type","pdf","pmid","doi")
        self.tree = ttk.Treeview(parent, columns=cols, show="headings",
                                  selectmode="browse")
        style = ttk.Style()
        style.configure("Treeview", background=BG2, foreground=FG,
                        fieldbackground=BG2, rowheight=32,
                        font=("Arial",9), borderwidth=0)
        style.configure("Treeview.Heading", background=BG3, foreground=GOLD,
                        font=("Courier",9,"bold"), relief="flat")
        style.map("Treeview",
                  background=[("selected","#2a2a1a")],
                  foreground=[("selected",GOLD)])
        for col,(hdr,w) in {
            "score":  ("Score", 55), "title":  ("Title", 310),
            "year":   ("Year",  52), "authors":("Authors",170),
            "type":   ("Type",  110),"pdf":    ("PDF",   45),
            "pmid":   ("PMID",  80), "doi":    ("DOI",   150),
        }.items():
            self.tree.heading(col, text=hdr)
            self.tree.column(col, width=w, minwidth=30,
                             anchor="w" if col in ("title","authors","doi") else "center")
        self.tree.tag_configure("high",   background="#1a1a0a", foreground="#c4a96a")
        self.tree.tag_configure("medium", background="#0a0f1a", foreground="#aabbdd")
        self.tree.tag_configure("low",    background="#141414", foreground="#888880")
        self.tree.tag_configure("none",   background="#141414", foreground="#666660")
        vsb = ttk.Scrollbar(parent, orient="vertical",   command=self.tree.yview)
        hsb = ttk.Scrollbar(parent, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        hsb.pack(side="bottom", fill="x")
        vsb.pack(side="right",  fill="y")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        det = tk.Frame(parent, bg=BG3, pady=10, padx=14); det.pack(fill="x")
        tk.Label(det, text="AI Summary & Details", font=("Courier",8),
                 fg=FG3, bg=BG3).pack(anchor="w")
        self.txt_detail = tk.Text(det, height=6, bg=BG3, fg=FG2,
                                   relief="flat", bd=0, font=("Georgia",10),
                                   wrap="word", state="disabled",
                                   insertbackground=GOLD)
        self.txt_detail.pack(fill="x")

    def _build_log_tab(self, parent):
        self.log_box = scrolledtext.ScrolledText(
            parent, bg=BG, fg=FG2, insertbackground=GOLD,
            font=("Courier",9), relief="flat", bd=0,
            wrap="word", state="disabled")
        self.log_box.pack(fill="both", expand=True, padx=2, pady=2)
        for tag,col in [("gold",GOLD),("green",GREEN),
                         ("red",RED),("blue",BLUE),("dim",FG3)]:
            self.log_box.tag_config(tag, foreground=col)

    # ── Ollama status ─────────────────────────────────────────────────────────
    def _check_ollama_status(self):
        model = self.v_model.get().strip() if hasattr(self,"v_model") else DEFAULT_MODEL
        ok, msg = check_ollama(model)
        if ok:
            self.lbl_ollama.config(text=f"● Ollama ready · {model}", fg=GREEN)
            self._log(f"Ollama ready. Model: {model}", "green")
        else:
            self.lbl_ollama.config(text="● Ollama offline", fg=RED)
            self._log(f"Ollama: {msg}", "red")
            self._log("If model is missing run:  ollama pull llama3.1:8b", "dim")

    # ── Logging ───────────────────────────────────────────────────────────────
    def _log(self, msg, tag=""):
        def _do():
            self.log_box.configure(state="normal")
            ts = datetime.datetime.now().strftime("%H:%M:%S")
            self.log_box.insert("end", f"[{ts}] ", "dim")
            self.log_box.insert("end", msg + "\n", tag or "")
            self.log_box.see("end")
            self.log_box.configure(state="disabled")
        self.after(0, _do)

    def _set_progress(self, val):
        self.after(0, lambda: self.progress.configure(value=val))

    # ── Results ───────────────────────────────────────────────────────────────
    def _render_results(self):
        sort = self.v_sort.get(); data = list(self._papers)
        if   sort == "Relevance":     data.sort(key=lambda p: self._summaries.get(p.get("pmid",""),{}).get("score",0), reverse=True)
        elif sort == "Year (newest)": data.sort(key=lambda p: p.get("year","0"), reverse=True)
        elif sort == "Year (oldest)": data.sort(key=lambda p: p.get("year","9999"))
        self.tree.delete(*self.tree.get_children())
        for p in data:
            pmid  = p.get("pmid",""); s = self._summaries.get(pmid,{})
            score = s.get("score","–")
            tag   = "none"
            if isinstance(score,int):
                tag = "high" if score>=7 else "medium" if score>=4 else "low"
            self.tree.insert("","end", iid=pmid or p.get("title","")[:20],
                             tags=(tag,), values=(
                score,
                p.get("title","")[:90],
                p.get("year",""),
                fmt_authors(p.get("authors",[]),2)[:38],
                s.get("paper_type", fmt_types(p.get("pub_types",[])))[:22],
                "Yes" if self._pdf_paths.get(pmid) else "No",
                pmid,
                p.get("doi","")[:38],
            ))
        n = len(data)
        self.after(0, lambda: self.lbl_count.config(
            text=f"{n} paper{'s' if n!=1 else ''} with full-text links"))

    def _on_select(self, ev):
        sel = self.tree.selection()
        if not sel: return
        iid = sel[0]
        p   = next((x for x in self._papers
                    if x.get("pmid")==iid or x.get("title","")[:20]==iid), None)
        if not p: return
        pmid = p.get("pmid","")
        s    = self._summaries.get(pmid, {})
        txt  = s.get("summary",
               "No AI summary yet — AI analysis may still be running or was skipped.")
        r    = s.get("reason","")
        doi  = p.get("doi",""); pdf = self._pdf_paths.get(pmid,"")
        if r:    txt += f"\n\nRelevance note: {r}"
        if doi:  txt += f"\n\nDOI: https://doi.org/{doi}"
        if pmid: txt += f"\nPubMed: https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        if pdf:  txt += f"\nSaved PDF: {pdf}"
        self.txt_detail.configure(state="normal")
        self.txt_detail.delete("1.0","end")
        self.txt_detail.insert("end", txt)
        self.txt_detail.configure(state="disabled")

    # ── Search flow ───────────────────────────────────────────────────────────
    def _start_search(self):
        query = self.v_query.get().strip()
        if not query:
            messagebox.showwarning("Veronica","Please enter keywords or a topic.")
            return
        if self._running: return
        self._running = True
        self.btn_search.configure(state="disabled", bg=GOLD_DIM)
        self.btn_stop.configure(state="normal")
        self._papers=[]; self._summaries={}; self._pdf_paths={}
        self.tree.delete(*self.tree.get_children())
        self.lbl_count.config(text="Searching PubMed…")
        threading.Thread(target=self._run_search, daemon=True).start()

    def _stop(self):
        self._running = False; self._log("Stopped by user.", "red")

    def _run_search(self):
        try:   self._search_impl()
        except Exception as e: self._log(f"Unexpected error: {e}", "red")
        finally:
            self._running = False
            self.after(0, lambda: self.btn_search.configure(state="normal", bg=GOLD))
            self.after(0, lambda: self.btn_stop.configure(state="disabled"))
            self._set_progress(0)

    def _search_impl(self):
        query    = self.v_query.get().strip()
        rq       = self.txt_rq.get("1.0","end").strip()
        year     = self.v_year.get().strip() or None
        fetch_n  = int(self.v_fetch.get())
        show_n   = int(self.v_show.get())
        arttype  = self.v_arttype.get().strip()
        model    = self.v_model.get().strip() or DEFAULT_MODEL
        do_pdf   = self.v_download.get()
        do_ai    = self.v_ai.get()
        do_xls   = self.v_excel.get()
        do_summ  = self.v_summary.get()

        # Add article type to query if specified
        full_query = query
        if arttype:
            full_query += f' AND "{arttype}"[Publication Type]'

        # 1. PubMed search
        self._log(f"Searching PubMed: '{full_query}'…", "gold")
        self._log("  (No rate limits — PubMed is free & unlimited)", "dim")
        self._set_progress(5)
        try:
            papers = pubmed_search(full_query, max_results=show_n, year_from=year)
        except Exception as e:
            self._log(f"PubMed search failed: {e}", "red"); return

        if not papers:
            self._log("No papers with abstracts + full-text links found.", "red")
            self._log("Try: broader keywords, remove year filter, or different article type.", "dim")
            self.after(0, lambda: self.lbl_count.config(text="No results")); return

        self._papers = papers
        self._log(f"Found {len(papers)} papers with full-text links from PubMed.", "green")
        self._set_progress(20)
        self.after(0, self._render_results)

        # 2. Make folder
        folder = make_folder(query); self._folder = folder
        self._log(f"Saving to: {folder}", "blue")

        # 3. Download PDFs
        if do_pdf and self._running:
            self._log(f"Downloading PDFs (PMC open-access papers)…", "gold")
            for i,p in enumerate(papers):
                if not self._running: break
                pmid = p.get("pmid","")
                path = download_pdf(p, folder, log_fn=self._log)
                self._pdf_paths[pmid] = path
                self._set_progress(20 + int(28*(i+1)/len(papers)))
                time.sleep(0.3)
            done = sum(1 for v in self._pdf_paths.values() if v)
            self._log(f"PDFs: {done}/{len(papers)} downloaded.", "green")
            self.after(0, self._render_results)

        # 4. Ollama AI analysis — paper by paper
        if do_ai and self._running:
            ok, omsg = check_ollama(model)
            if not ok:
                self._log(f"Ollama not available: {omsg}", "red")
                self._log("Start Ollama:  ollama serve", "dim")
            elif not rq:
                self._log("No research question entered — skipping AI analysis.", "dim")
            else:
                self._log(f"Analyzing {len(papers)} papers with Ollama ({model})…", "gold")
                self._log("Each paper takes ~15–40 sec. Results appear as they complete.", "dim")
                for i,p in enumerate(papers):
                    if not self._running: break
                    pmid = p.get("pmid","")
                    self._log(f"  [{i+1}/{len(papers)}] {p.get('title','')[:60]}…")
                    result = analyze_paper_ollama(p, rq, model, log_fn=self._log)
                    if result:
                        self._summaries[pmid] = result
                        sc = result.get("score","?")
                        pt = result.get("paper_type","")
                        self._log(f"      ✓ Score {sc}/10  |  {pt}", "green")
                    else:
                        self._log("      Could not parse model response.", "dim")
                    self._set_progress(50 + int(38*(i+1)/len(papers)))
                    self.after(0, self._render_results)
                self._log(f"AI analysis complete: {len(self._summaries)}/{len(papers)} scored.", "green")

        # 5. Save Excel
        self._set_progress(92)
        if do_xls and self._running:
            self._log("Saving Papers Excel…", "gold")
            try:
                pf = save_papers_xlsx(papers, folder, query, self._pdf_paths)
                self._log(f"Saved: {pf.name}", "green")
            except Exception as e:
                self._log(f"Excel error: {e}", "red")

        if do_summ and self._running:
            self._log("Saving Summaries Excel…", "gold")
            try:
                sf = save_summaries_xlsx(papers, self._summaries, folder, query)
                self._log(f"Saved: {sf.name}", "green")
            except Exception as e:
                self._log(f"Excel error: {e}", "red")

        self._set_progress(100)
        self._log("─" * 70)
        self._log(f"Done!  All files saved to: {folder}", "green")
        self._log("─" * 70)
        self.after(0, self._render_results)

    # ── Open folder ───────────────────────────────────────────────────────────
    def _open_folder(self):
        target = self._folder or BASE_DIR
        target.mkdir(parents=True, exist_ok=True)
        if sys.platform == "win32":    os.startfile(target)
        elif sys.platform == "darwin": os.system(f'open "{target}"')
        else:                          os.system(f'xdg-open "{target}"')


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = VeronicaApp()
    app.mainloop()
