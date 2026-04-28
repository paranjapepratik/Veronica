# Veronica 🔬
### AI-Powered Literature Review Tool

Veronica is a free, fully local desktop application for researchers and students to **search, analyze, download, and organize academic papers** — powered by PubMed and Ollama AI.

No API keys. No subscriptions. No data leaves your machine.

---

## ✨ Features

- 🔍 **PubMed Search** — searches 35+ million biomedical papers, free and unlimited
- 🤖 **Local AI Analysis** — uses Ollama (llama3.1:8b) to score each paper's relevance to your research question, classify paper type, and write a plain-English summary
- 📄 **Full-Text PDF Download** — automatically downloads open-access PDFs from PubMed Central
- 📊 **Excel Reports** — saves two organized Excel files per search:
  - `Papers_topic_date.xlsx` — all papers with DOI, PMID, authors, journal, citations
  - `Summaries_topic_date.xlsx` — AI summaries and relevance scores (color-coded)
- 🗂️ **Auto-organized folders** — saves everything to `Desktop/Veronica/YYYY-MM-DD/topic/`
- 🖥️ **Desktop GUI** — clean dark-themed interface, no command line needed after setup

---

## 🖥️ Screenshot

```
┌─────────────────────────────────────────────────────────────┐
│  Veronica  ·  AI Literature Review          v3.0 · PubMed  │
├──────────────────────┬──────────────────────────────────────┤
│  SEARCH              │  Results  │  Log                     │
│  Keywords / Topic    │                                      │
│  [               ]   │  Score  Title          Year  Type    │
│                      │  9/10   Alzheimer...   2023  Review  │
│  Research Question   │  8/10   CRISPR...      2022  Paper   │
│  [               ]   │  7/10   Mice model...  2021  Paper   │
│                      │                                      │
│  Min Year: [2015]    │  AI Summary & Details                │
│  Fetch:    [50  ]    │  This paper investigates...          │
│  Show Top: [10  ]    │                                      │
│  [Search & Analyze]  │                                      │
└──────────────────────┴──────────────────────────────────────┘
```

---

## ⚙️ Requirements

- Python 3.9 or newer
- [Ollama](https://ollama.com) installed locally

---

## 🚀 Installation

**1. Clone this repository**
```bash
git clone https://github.com/paranjapepratik/Veronica.git
cd Veronica
```

**2. Install Python dependencies**
```bash
pip3 install requests openpyxl biopython
```

**3. Install Ollama and download the AI model**
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.1:8b
```

**4. Install tkinter (Linux only)**
```bash
sudo apt-get install python3-tk -y
```

**5. Run Veronica**
```bash
python3 veronica.py
```

---

## 📖 How to Use

1. **Enter keywords** in the search box
   - Example: `alzheimer disease mild cognitive impairment mouse model`

2. **Enter your research question** — Ollama uses this to score each paper's relevance
   - Example: `What mouse models are used to study mild cognitive impairment in Alzheimer's disease?`

3. **Set filters** (optional)
   - Min Year: e.g. `2015`
   - Article Type: `Review`, `Clinical Trial`, `Meta-Analysis`

4. **Click Search & Analyze**
   - Veronica searches PubMed, downloads available PDFs, runs AI analysis, and saves Excel files

5. **Click any paper** in the results table to read its AI summary in the detail pane

6. **Click "Open Output Folder"** to access your downloaded PDFs and Excel files

---

## 📁 Output Structure

```
Desktop/
└── Veronica/
    └── 2025-01-28/
        └── alzheimer disease mouse model/
            ├── 2023_Title_of_Paper.pdf
            ├── 2022_Another_Paper.pdf
            ├── Papers_alzheimer_2025-01-28.xlsx
            └── Summaries_alzheimer_2025-01-28.xlsx
```

---

## 🧠 AI Scoring

Each paper is scored by Ollama against your research question:

| Score | Meaning | Color |
|-------|---------|-------|
| 7–10  | Highly relevant | 🟡 Gold |
| 4–6   | Moderately relevant | 🔵 Blue |
| 1–3   | Low relevance | ⚫ Gray |

---

## 🔧 Changing the AI Model

You can use any model you've pulled with Ollama. Just type the model name in the **Ollama Model** field:

```bash
ollama pull mistral        # 7B, great for research
ollama pull llama3.2       # 3B, faster, less RAM
ollama pull llama3.1:8b    # default, best balance
```

---

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| `biopython` | PubMed / Entrez API access |
| `requests` | HTTP calls to Ollama |
| `openpyxl` | Excel file creation |
| `tkinter` | Desktop GUI (bundled with Python) |
| `ollama` | Local AI model runner |

---

## 🙏 Acknowledgements

- [PubMed / NCBI Entrez](https://www.ncbi.nlm.nih.gov/home/develop/api/) — free biomedical literature database
- [Ollama](https://ollama.com) — local AI model runner
- [Meta LLaMA 3.1](https://llama.meta.com) — open-source language model

---

## 📄 License

MIT License — free to use, modify, and share.

---

*Built for researchers who want powerful literature review tools without paywalls or privacy concerns.*
