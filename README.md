# NeuroRisk GRC ⬡
**AI-powered compliance gap analysis and GRC intelligence platform.**

NeuroRisk analyses your company's policy documents against 8 major regulatory frameworks using RAG (Retrieval-Augmented Generation) — surfacing gaps, coverage scores, and actionable remediation plans in seconds.

---

## What It Does

- **Gap Analysis** — compares your uploaded documents clause-by-clause against regulatory frameworks, returning coverage %, matched requirements, and specific gaps with remediation steps
- **Compliance Chat** — ask Eva AI anything about your compliance posture; answers are grounded in your documents and the loaded frameworks via TF-IDF retrieval
- **Full Posture Analysis** — aggregate coverage scores across all uploaded docs and all frameworks
- **SQLite Persistence** — gap results and company documents persist across session reloads

---

## Supported Frameworks

| Framework | Focus Area |
|---|---|
| RBI AI Framework | AI governance for Indian financial institutions |
| NIST CSF | Cybersecurity risk management |
| ISO 27001 | Information security management |
| Basel III | Banking capital and risk standards |
| DPDP Act | India's Digital Personal Data Protection Act |
| RBI Master Direction | RBI IT governance and cyber security directions |
| SEBI CSCRF | SEBI cyber security and cyber resilience framework |
| Control Library | Internal control reference library |

---

## Project Structure

```
neu/
├── app.py                        # Streamlit entry point
├── .env                          # API keys (not committed)
├── requirements.txt
└── neurisk/
    ├── __init__.py
    ├── neurisk_ui.py             # Streamlit UI — sidebar, pages, gap results renderer
    ├── rag_engine.py             # RAG engine — LLM calls, TF-IDF retrieval, SQLite persistence
    ├── neurisk_sessions.db       # Auto-generated session DB (not committed)
    └── documents/                # Place framework PDFs here (not committed)
        ├── rbi_ai_framework.pdf
        ├── nist_csf.pdf
        ├── iso_27001.pdf
        ├── basel_3.pdf
        ├── dpdp_act.pdf
        ├── rbi_master_direction.pdf
        ├── sebi_cscrf.pdf
        └── control_library.pdf
```

---

## How It Works

1. **Framework Loading** (`rag_engine.py`) — on startup, extracts text from all 8 PDFs using PyMuPDF, with OCR fallback via pytesseract for scanned documents. Text is chunked and stored in session state.

2. **Gap Analysis** — for each selected framework, a single LLM call is made with:
   - First 1500 words of the company document
   - First 2000 words of the framework
   - A strict auditor-persona system prompt
   - Returns matched requirements, gaps, coverage %, and remediation plans — all in one JSON response

3. **Parallelism** — up to 4 frameworks analysed simultaneously via `ThreadPoolExecutor`

4. **TF-IDF Retrieval** (Compliance Chat) — `scikit-learn` TF-IDF vectorizer ranks framework chunks by cosine similarity to the user's question; top-K chunks fed to the LLM

5. **Persistence** — gap results, document registry, and document text stored in SQLite (`neurisk_sessions.db`) keyed by Streamlit session ID

---

## Setup

### 1. Clone
```bash
git clone https://github.com/harithaharikumar100-gif/neurisk.git
cd neurisk
```

### 2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Add framework PDFs
Place all 8 framework PDFs in `neurisk/documents/` — filenames must match exactly:
```
rbi_ai_framework.pdf
nist_csf.pdf
iso_27001.pdf
basel_3.pdf
dpdp_act.pdf
rbi_master_direction.pdf
sebi_cscrf.pdf
control_library.pdf
```

### 5. Create `.env`
```env
OPENROUTER_API_KEY=your_openrouter_api_key
```
Get a free key at [openrouter.ai](https://openrouter.ai)

### 6. Run
```bash
streamlit run app.py
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| UI | Streamlit |
| LLM | OpenRouter (`openrouter/free` — any model) |
| LLM Client | OpenAI SDK (pointed at OpenRouter base URL) |
| PDF Extraction | PyMuPDF (`fitz`) + pytesseract OCR fallback |
| Retrieval | scikit-learn TF-IDF + cosine similarity |
| Parallelism | `concurrent.futures.ThreadPoolExecutor` |
| Persistence | SQLite via `sqlite3` |
| DOCX Support | python-docx |

---

## Requirements

```
streamlit
openai
python-dotenv
scikit-learn
pymupdf
python-docx
pdf2image
pytesseract
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `OPENROUTER_API_KEY` | ✅ | OpenRouter API key for LLM inference |

---

## Pages

| Page | Description |
|---|---|
| Overview | Framework load status, company doc count, system health |
| Upload Documents | Upload PDF/DOCX/TXT/MD files or paste text directly |
| Gap Analysis | Select document + frameworks → run clause-level audit |
| Compliance Chat | Ask Eva AI questions grounded in your documents and frameworks |

---

## Notes

- Framework PDFs are not committed to the repo — add them manually to `neurisk/documents/`
- The session database (`neurisk_sessions.db`) is auto-created on first run and is not committed
- OCR fallback activates automatically if PyMuPDF extracts fewer than 300 characters from a PDF
- LLM calls include automatic retry logic (up to 3 attempts) with self-correction prompts for malformed JSON

---


## License

Proprietary. Do not distribute without permission.
