"""
neurisk/rag_engine.py
─────────────────────
NeuroRisk RAG engine — v6 (OpenRouter API + single-pass gap analysis)

Setup:
  1. Get a free API key from https://openrouter.ai
  2. Add to .env file: OPENROUTER_API_KEY=your_key_here
  3. pip install openai

Exposes:
  load_frameworks()         → dict[name, loaded_bool]
  add_company_doc()         → None
  get_company_docs()        → dict[name, text]
  get_frameworks()          → dict[name, text]
  company_has_docs()        → bool
  clear_company_docs()      → None
  extract_uploaded_file()   → str
  gap_analysis()            → list[dict] | None
  compliance_chat()         → str
  full_posture_analysis()   → dict[framework, avg_pct]
  get_gap_history()         → list[dict]
  FRAMEWORKS                → dict[name, filename]
"""

import os, re, json, pathlib, sqlite3, hashlib, datetime
import streamlit as st
import time
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()   

# ── OpenRouter config ─────────────────────────────────────────────────────────
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

OPENROUTER_MODEL = "openrouter/free"

# Add to imports at top of rag_engine.py



def _check_api() -> bool:
    """Check if OpenRouter API key is configured and working."""
    if not os.getenv("OPENROUTER_API_KEY"):
        return False
    try:
        client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[{"role": "user", "content": "test"}],
            max_tokens=5,
        )
        return True
    except Exception:
        return False


def _llm(prompt: str, system: str = "", max_tokens: int = 8192) -> str:
    """Call OpenRouter and return raw text."""
    if not os.getenv("OPENROUTER_API_KEY"):
        return "[LLM error: OPENROUTER_API_KEY not set in .env file]"
    try:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=messages,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"[LLM error: {e}]"


def _llm_json(prompt: str,
              system: str = "",
              max_tokens: int = 8192,
              retries: int = 2) -> dict | list | None:
    last_raw = ""
    for attempt in range(retries + 1):
        if attempt > 0:
            time.sleep(2 * attempt)   # wait 2s, then 4s, etc. before retrying

        if attempt == 0:
            raw = _llm(prompt, system, max_tokens)
        else:
            correction_prompt = (
                f"Your previous response was not valid JSON.\n\n"
                f"Previous response:\n{last_raw}\n\n"
                f"Return ONLY the corrected JSON object. "
                f"Start your response with {{ and end with }}. "
                f"No explanation, no markdown, no extra text whatsoever."
            )
            raw = _llm(correction_prompt, system, max_tokens)
        # ...rest unchanged raw = _llm(correction_prompt, system, max_tokens)

        last_raw = raw

        if raw.startswith("[LLM error"):
            continue

        clean = re.sub(r"```(?:json)?|```", "", raw).strip()

        try:
            return json.loads(clean)
        except Exception:
            pass

        try:
            start = clean.index("{")
            end   = clean.rindex("}") + 1
            return json.loads(clean[start:end])
        except Exception:
            pass

        try:
            start = clean.index("[")
            end   = clean.rindex("]") + 1
            return json.loads(clean[start:end])
        except Exception:
            pass

    return None


# ── Framework definitions ─────────────────────────────────────────────────────
FRAMEWORKS = {
    "RBI AI Framework":     "rbi_ai_framework.pdf",
    "NIST CSF":             "nist_csf.pdf",
    "ISO 27001":            "iso_27001.pdf",
    "Basel III":            "basel_3.pdf",
    "DPDP Act":             "dpdp_act.pdf",
    "RBI Master Direction": "rbi_master_direction.pdf",
    "SEBI CSCRF":           "sebi_cscrf.pdf",
    "Control Library":      "control_library.pdf",
}

DOCS_DIR = pathlib.Path(__file__).parent / "documents"
DB_PATH  = pathlib.Path(__file__).parent / "neurisk_sessions.db"

CHUNK_SIZE        = 400
CHUNK_OVERLAP     = 50
TOP_K_CHUNKS      = 6
MAX_CHUNK_CHARS   = 3000
MAX_FW_WORDS      = 2000
DOC_EXCERPT_WORDS = 1500


# ═══════════════════════════════════════════════════════════════════════════════
# TEXT EXTRACTION
# ═══════════════════════════════════════════════════════════════════════════════

def _extract_pdf_pymupdf(path_or_bytes, is_bytes=False) -> str:
    try:
        import fitz
        doc = (fitz.open(stream=path_or_bytes, filetype="pdf")
               if is_bytes else fitz.open(str(path_or_bytes)))
        return "\n".join(page.get_text() for page in doc).strip()
    except ImportError:
        return ""
    except Exception:
        return ""


def _extract_pdf_ocr(path_or_bytes, is_bytes=False) -> str:
    try:
        from pdf2image import convert_from_bytes, convert_from_path
        import pytesseract
        images = (convert_from_bytes(path_or_bytes)
                  if is_bytes else convert_from_path(str(path_or_bytes)))
        return "\n".join(pytesseract.image_to_string(img) for img in images).strip()
    except ImportError:
        return "[OCR unavailable — pip install pytesseract pdf2image]"
    except Exception as e:
        return f"[OCR error: {e}]"


def _extract_pdf(path_or_bytes, is_bytes=False) -> str:
    text = _extract_pdf_pymupdf(path_or_bytes, is_bytes)
    if len(text.strip()) < 300:
        ocr_text = _extract_pdf_ocr(path_or_bytes, is_bytes)
        if len(ocr_text.strip()) > len(text.strip()):
            return ocr_text
    return text


def _extract_docx(data: bytes) -> str:
    try:
        import docx, io
        d = docx.Document(io.BytesIO(data))
        return "\n".join(p.text for p in d.paragraphs).strip()
    except ImportError:
        return "[python-docx not installed — pip install python-docx]"
    except Exception as e:
        return f"[DOCX error: {e}]"


def extract_uploaded_file(uploaded_file) -> str:
    data = uploaded_file.read()
    name = uploaded_file.name.lower()
    if name.endswith(".pdf"):
        return _extract_pdf(data, is_bytes=True)
    elif name.endswith(".docx"):
        return _extract_docx(data)
    else:
        return data.decode("utf-8", errors="ignore")


# ═══════════════════════════════════════════════════════════════════════════════
# CHUNKING  (compliance_chat only)
# ═══════════════════════════════════════════════════════════════════════════════

def _chunk_text(text: str,
                chunk_size: int = CHUNK_SIZE,
                overlap: int = CHUNK_OVERLAP) -> list[str]:
    words  = text.split()
    chunks = []
    step   = max(1, chunk_size - overlap)
    for i in range(0, len(words), step):
        chunk = " ".join(words[i : i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks


# ═══════════════════════════════════════════════════════════════════════════════
# TF-IDF RETRIEVAL  (compliance_chat only)
# ═══════════════════════════════════════════════════════════════════════════════

def _retrieve_chunks(query: str,
                     chunks: list[str],
                     top_k: int = TOP_K_CHUNKS) -> list[str]:
    if not chunks:
        return []
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np
        corpus     = chunks + [query]
        vectorizer = TfidfVectorizer(stop_words="english", max_features=8000)
        matrix     = vectorizer.fit_transform(corpus)
        scores     = cosine_similarity(matrix[-1], matrix[:-1])[0]
        top_idx    = np.argsort(scores)[::-1][:top_k]
        return [chunks[i] for i in sorted(top_idx)]
    except ImportError:
        return chunks[:top_k]


def _retrieve_for_query(query: str,
                        fw_names: list[str] | None = None,
                        top_k: int = TOP_K_CHUNKS) -> str:
    store        = _store()
    chunks_store = store["fw_chunks"]
    target       = fw_names if fw_names else list(chunks_store.keys())
    parts        = []
    for name in target:
        if name not in chunks_store:
            continue
        relevant = _retrieve_chunks(query, chunks_store[name], top_k=top_k)
        if relevant:
            joined = "\n---\n".join(relevant)
            if len(joined) > MAX_CHUNK_CHARS:
                joined = joined[:MAX_CHUNK_CHARS] + "\n[...truncated]"
            parts.append(f"=== {name} ===\n{joined}")
    return "\n\n".join(parts)


# ═══════════════════════════════════════════════════════════════════════════════
# SQLITE PERSISTENCE
# ═══════════════════════════════════════════════════════════════════════════════

def _init_db():
    con = sqlite3.connect(str(DB_PATH))
    con.executescript("""
        CREATE TABLE IF NOT EXISTS gap_results (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id      TEXT NOT NULL,
            doc_name        TEXT NOT NULL,
            framework       TEXT NOT NULL,
            status          TEXT,
            coverage_pct    INTEGER,
            matched         TEXT,
            gaps            TEXT,
            recommendation  TEXT,
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS doc_registry (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  TEXT NOT NULL,
            doc_name    TEXT NOT NULL,
            char_count  INTEGER,
            doc_hash    TEXT,
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS doc_texts (
            session_id  TEXT NOT NULL,
            doc_name    TEXT NOT NULL,
            text        TEXT NOT NULL,
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (session_id, doc_name)
        );
    """)
    con.commit()
    con.close()


def _session_id() -> str:
    try:
        return st.runtime.scriptrunner.get_script_run_ctx().session_id
    except Exception:
        return hashlib.md5(str(datetime.datetime.now()).encode()).hexdigest()[:12]


def _save_gap_results(doc_name: str, results: list[dict]):
    try:
        _init_db()
        sid = _session_id()
        con = sqlite3.connect(str(DB_PATH))
        for r in results:
            con.execute("""
                INSERT INTO gap_results
                  (session_id, doc_name, framework, status, coverage_pct,
                   matched, gaps, recommendation)
                VALUES (?,?,?,?,?,?,?,?)
            """, [
                sid,
                doc_name,
                r.get("framework", ""),
                r.get("status", ""),
                r.get("coverage_percent", 0),
                json.dumps(r.get("matched_requirements", [])),
                json.dumps(r.get("gaps", [])),
                json.dumps(r.get("recommendation", "")),
            ])
        con.commit()
        con.close()
    except Exception:
        pass


def _save_doc_metadata(doc_name: str, text: str):
    try:
        _init_db()
        sid = _session_id()
        h   = hashlib.md5(text.encode()).hexdigest()[:12]
        con = sqlite3.connect(str(DB_PATH))
        con.execute("""
            INSERT INTO doc_registry (session_id, doc_name, char_count, doc_hash)
            VALUES (?,?,?,?)
        """, [sid, doc_name, len(text), h])
        con.commit()
        con.close()
    except Exception:
        pass


def _save_doc_text(doc_name: str, text: str):
    try:
        _init_db()
        sid = _session_id()
        con = sqlite3.connect(str(DB_PATH))
        con.execute("""
            INSERT OR REPLACE INTO doc_texts (session_id, doc_name, text)
            VALUES (?, ?, ?)
        """, [sid, doc_name, text])
        con.commit()
        con.close()
    except Exception:
        pass


def _load_persisted_docs():
    try:
        _init_db()
        sid  = _session_id()
        con  = sqlite3.connect(str(DB_PATH))
        rows = con.execute("""
            SELECT doc_name, text FROM doc_texts WHERE session_id = ?
        """, [sid]).fetchall()
        con.close()
        store = _store()
        for doc_name, text in rows:
            if doc_name not in store["company"]:
                store["company"][doc_name] = text
    except Exception:
        pass


def get_gap_history(limit: int = 50) -> list[dict]:
    try:
        _init_db()
        con  = sqlite3.connect(str(DB_PATH))
        rows = con.execute("""
            SELECT doc_name, framework, status, coverage_pct,
                   recommendation, created_at
            FROM gap_results
            ORDER BY created_at DESC
            LIMIT ?
        """, [limit]).fetchall()
        con.close()
        return [
            {
                "doc_name":         r[0],
                "framework":        r[1],
                "status":           r[2],
                "coverage_percent": r[3],
                "recommendation":   r[4],
                "created_at":       r[5],
            }
            for r in rows
        ]
    except Exception:
        return []


# ═══════════════════════════════════════════════════════════════════════════════
# SESSION STATE STORE
# ═══════════════════════════════════════════════════════════════════════════════

def _store() -> dict:
    if "neurisk" not in st.session_state:
        st.session_state.neurisk = {
            "frameworks":  {},
            "fw_chunks":   {},
            "company":     {},
            "fw_loaded":   False,
            "load_status": {},
        }
    return st.session_state.neurisk


# ═══════════════════════════════════════════════════════════════════════════════
# FRAMEWORK LOADING
# ═══════════════════════════════════════════════════════════════════════════════

def load_frameworks() -> dict[str, bool]:
    store  = _store()
    status = {}
    _load_persisted_docs()

    if store["fw_loaded"]:
        for name in FRAMEWORKS:
            status[name] = name in store["frameworks"]
        return status

    for name, filename in FRAMEWORKS.items():
        fpath = DOCS_DIR / filename
        if not fpath.exists():
            status[name] = False
            continue
        text = _extract_pdf(fpath)
        if not text or text.startswith("[") or len(text.strip()) < 100:
            status[name] = False
            continue
        chunks = _chunk_text(text)
        store["frameworks"][name] = text
        store["fw_chunks"][name]  = chunks
        status[name] = True

    store["fw_loaded"]   = True
    store["load_status"] = status
    return status


def add_company_doc(label: str, text: str):
    _store()["company"][label] = text
    _save_doc_metadata(label, text)
    _save_doc_text(label, text)


def get_company_docs() -> dict:
    return _store()["company"]


def get_frameworks() -> dict:
    return _store()["frameworks"]


def company_has_docs() -> bool:
    return bool(_store()["company"])


def clear_company_docs():
    _store()["company"].clear()
    try:
        _init_db()
        sid = _session_id()
        con = sqlite3.connect(str(DB_PATH))
        con.execute("DELETE FROM doc_texts WHERE session_id = ?", [sid])
        con.commit()
        con.close()
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════════════
# PROMPTS
# ═══════════════════════════════════════════════════════════════════════════════

_GAP_SYSTEM = """You are a senior ISO 27001 Lead Auditor and GRC consultant 
with 15+ years of experience. You produce precise, clause-level gap analyses 
with actionable remediation plans.

ABSOLUTE RULES:
1. Cite ONLY clauses present in the FRAMEWORK TEXT provided. Never invent clauses.
2. Every gap and matched entry must include the exact clause number AND name.
3. Every recommendation must start with an action verb and explain WHAT to do 
   and HOW to do it.
4. Return ONLY valid JSON — no markdown fences, no preamble, no extra text.
5. Do NOT add any explanation before or after the JSON."""

_SINGLE_PASS_PROMPT = """You are auditing the company document below against 
the provided regulatory framework.

COMPANY: {company_name}
DOCUMENT: "{doc_name}"
FRAMEWORK: {fw_name}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COMPANY DOCUMENT (excerpt):
{doc_excerpt}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FRAMEWORK TEXT (cite ONLY from this):
{fw_excerpt}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TASK — for EVERY clause or requirement in the framework text:
  A) Check whether the company document addresses it.
  B) If addressed  → add to matched_requirements
  C) If NOT addressed → add to gaps AND write a specific recommendation

Return ONLY this JSON object, nothing else, no other text before or after:
{{
  "matched_requirements": [
    {{
      "clause":   "<Clause X.X — Name>",
      "location": "<section in the company doc where this is covered>",
      "summary":  "<one sentence: how the doc addresses this>"
    }}
  ],
  "gaps": [
    {{
      "clause":          "<Clause X.X — Name>",
      "what_is_missing": "<specific element the doc lacks>",
      "why_it_matters":  "<risk or regulatory consequence>",
      "recommendation": {{
        "action":   "<verb-led instruction: Draft/Create/Implement/Define/Establish/Document/Develop>",
        "how_to":   "<concrete steps, who owns it, what to include>",
        "add_to":   "<existing section to update OR new section name>",
        "priority": "Critical | High | Medium | Low",
        "timeline": "30 days | 60 days | 90 days"
      }}
    }}
  ],
  "coverage_percent": <integer 0-100, nearest 5>
}}"""

_CHAT_SYSTEM = """You are NeuroRisk AI, an expert compliance and GRC assistant 
specialising in financial services, cybersecurity, and data protection frameworks.
Answer questions concisely, cite specific clauses where relevant, and always 
ground your answer in the provided context."""


# ═══════════════════════════════════════════════════════════════════════════════
# CORE GAP ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

def _gap_analysis_single_framework(
    doc_name:     str,
    doc_text:     str,
    fw_name:      str,
    fw_text:      str,
    company_name: str,
    progress_callback=None,
) -> dict:
    """One LLM call per framework — gaps + recommendations in one response."""

    doc_excerpt = " ".join(doc_text.split()[:DOC_EXCERPT_WORDS])
    fw_excerpt  = " ".join(fw_text.split()[:MAX_FW_WORDS])

    if progress_callback:
        progress_callback(fw_name, 1, 1)

    prompt = _SINGLE_PASS_PROMPT.format(
        doc_name     = doc_name,
        company_name = company_name,
        fw_name      = fw_name,
        doc_excerpt  = doc_excerpt,
        fw_excerpt   = fw_excerpt,
    )

    result = _llm_json(prompt, system=_GAP_SYSTEM, max_tokens=8000, retries=3)

    if not result or not isinstance(result, dict):
        return {
            "framework":            fw_name,
            "status":               "Error",
            "coverage_percent":     0,
            "matched_requirements": [],
            "gaps": [{
                "clause":          "N/A",
                "what_is_missing": "LLM returned no parseable JSON",
                "why_it_matters":  "Analysis could not be completed",
                "recommendation":  {},
            }],
            "recommendation": {
                "priority": "Unknown",
                "action":   "Retry the analysis",
                "timeline": "Immediately",
            },
        }

    matched  = result.get("matched_requirements", [])
    gaps     = result.get("gaps", [])
    coverage = result.get("coverage_percent", 0)
    if not isinstance(coverage, (int, float)):
        coverage = 0
    coverage = round(round(int(coverage) / 5) * 5)

    if coverage >= 80:
        status = "Full"
    elif coverage >= 40:
        status = "Partial"
    else:
        status = "Gap"

    if gaps:
        actions = []
        for i, g in enumerate(gaps, 1):
            rec  = g.get("recommendation", {})
            line = (
                f"{i}. {g.get('clause', 'Unknown clause')}: "
                f"{rec.get('action', '')} — "
                f"{rec.get('how_to', '')} "
                f"[Add to: {rec.get('add_to', 'N/A')}] "
                f"[{rec.get('priority', 'Medium')} | {rec.get('timeline', '60 days')}]"
            )
            actions.append(line)

        priorities   = [g.get("recommendation", {}).get("priority", "Medium") for g in gaps]
        top_priority = (
            "Critical" if "Critical" in priorities else
            "High"     if "High"     in priorities else
            "Medium"   if "Medium"   in priorities else
            "Low"
        )
        timelines    = [g.get("recommendation", {}).get("timeline", "60 days") for g in gaps]
        top_timeline = (
            "30 days" if "30 days" in timelines else
            "60 days" if "60 days" in timelines else
            "90 days"
        )
        consolidated_rec = {
            "priority":                    top_priority,
            "action":                      "\n".join(actions),
            "timeline":                    top_timeline,
            "references_existing_section": ", ".join(
                g.get("recommendation", {}).get("add_to", "")
                for g in gaps
                if g.get("recommendation", {}).get("add_to")
            ) or "New sections required",
        }
    else:
        consolidated_rec = {
            "priority":                    "Low",
            "action":                      "No gaps identified.",
            "timeline":                    "N/A",
            "references_existing_section": "N/A",
        }

    return {
        "framework":            fw_name,
        "status":               status,
        "coverage_percent":     coverage,
        "matched_requirements": matched,
        "gaps":                 gaps,
        "recommendation":       consolidated_rec,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════

def gap_analysis(doc_name: str,
                 selected_frameworks: list[str],
                 progress_callback=None) -> list[dict] | None:
    """
    Run gap analysis for one company document against selected frameworks.
    Uses ONE LLM call per framework, run in parallel (max 4 at a time).
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    company = get_company_docs()
    if doc_name not in company:
        return None

    if not os.getenv("OPENROUTER_API_KEY"):
        st.error(
            "❌ OpenRouter API key not found.\n\n"
            "Please:\n"
            "1. Get a free key from https://openrouter.ai\n"
            "2. Add to your .env file: OPENROUTER_API_KEY=your_key_here\n"
            "3. Restart the app and retry."
        )
        return None

    doc_text     = company[doc_name]
    fw_store     = _store()["frameworks"]
    company_name = st.session_state.get("nr_company_name", "The Company")
    results      = []

    def run_one(fw_name: str) -> dict | None:
            if fw_name not in fw_store:
                return None

            last_result = None
            for attempt in range(2):  # try up to twice per framework
                try:
                    result = _gap_analysis_single_framework(
                        doc_name          = doc_name,
                        doc_text          = doc_text,
                        fw_name           = fw_name,
                        fw_text           = fw_store[fw_name],
                        company_name      = company_name,
                        progress_callback = progress_callback,
                    )
                    if result.get("status") != "Error":
                        return result
                    last_result = result
                except Exception as e:
                    last_result = {
                        "framework":            fw_name,
                        "status":               "Error",
                        "coverage_percent":     0,
                        "matched_requirements": [],
                        "gaps": [{
                            "clause":          "N/A",
                            "what_is_missing": f"Analysis failed: {e}",
                            "why_it_matters":  "Cannot determine compliance status",
                            "recommendation":  {
                                "action":   "Retry the analysis",
                                "how_to":   "Check OpenRouter API key and retry",
                                "add_to":   "N/A",
                                "priority": "High",
                                "timeline": "Immediately",
                            },
                        }],
                        "recommendation": {
                            "priority":                    "Unknown",
                            "action":                      "Retry the analysis",
                            "timeline":                    "Immediately",
                            "references_existing_section": "N/A",
                        },
                    }

                if attempt == 0:
                    time.sleep(2)  # brief pause before retrying this framework

            return last_result
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(run_one, fw): fw
            for fw in selected_frameworks
        }
        for future in as_completed(futures):
            result = future.result()
            if result is not None:
                results.append(result)

    # Sort results to match original selected_frameworks order
    order = {fw: i for i, fw in enumerate(selected_frameworks)}
    results.sort(key=lambda r: order.get(r.get("framework", ""), 999))

    if results:
        _save_gap_results(doc_name, results)
    return results if results else None
def compliance_chat(question: str, history: list[dict]) -> str:
    """
    Multi-turn compliance Q&A backed by TF-IDF retrieval over framework chunks.
    history = [{"role": "user"|"assistant", "content": "..."}]
    """
    fw_context = _retrieve_for_query(question, top_k=TOP_K_CHUNKS)

    co_parts = []
    for name, text in get_company_docs().items():
        excerpt = " ".join(text.split()[:1200])
        co_parts.append(f"=== {name} ===\n{excerpt}")
    co_context = "\n\n".join(co_parts)

    context_block = ""
    if fw_context:
        context_block += f"## RELEVANT FRAMEWORK EXCERPTS\n{fw_context}\n\n"
    if co_context:
        context_block += f"## COMPANY DOCUMENTS\n{co_context}\n\n"

    conversation_parts = []
    if context_block:
        conversation_parts.append(f"CONTEXT:\n{context_block}\n---")

    for turn in history[-6:]:
        role    = turn["role"].upper()
        content = turn["content"]
        conversation_parts.append(f"{role}: {content}")

    conversation_parts.append(f"USER: {question}")
    conversation_parts.append("ASSISTANT:")

    full_prompt = "\n\n".join(conversation_parts)
    return _llm(full_prompt, system=_CHAT_SYSTEM, max_tokens=1400)

# ═══════════════════════════════════════════════════════════════════════════════
# DEBUG
# ═══════════════════════════════════════════════════════════════════════════════

def debug_llm_test() -> dict:
    """Call this from your Streamlit UI to diagnose the exact failure."""
    results = {}
    
    key = os.getenv("OPENROUTER_API_KEY")
    results["api_key_found"] = bool(key)
    results["api_key_preview"] = key[:12] + "..." if key else "MISSING"
    
    try:
        raw = _llm("Say hello in one word.", max_tokens=10)
        results["basic_call"] = raw
    except Exception as e:
        results["basic_call"] = f"FAILED: {e}"
    
    try:
        raw = _llm('Return ONLY this exact JSON, nothing else: {"test": "ok"}', max_tokens=50)
        results["raw_json_response"] = raw
    except Exception as e:
        results["raw_json_response"] = f"FAILED: {e}"

    fw = get_frameworks()
    results["frameworks_loaded"] = list(fw.keys())
    
    co = get_company_docs()
    results["company_docs"] = list(co.keys())
    
    return results
def full_posture_analysis() -> dict[str, float]:
    """
    Aggregate coverage scores across all uploaded docs and all frameworks.
    Returns {framework_name: average_coverage_percent}
    """
    all_docs = get_company_docs()
    fw_names = list(get_frameworks().keys())

    if not all_docs or not fw_names:
        return {}

    aggregate: dict[str, list[int]] = {}

    for doc_name in all_docs:
        results = gap_analysis(doc_name, fw_names)
        if not results:
            continue
        for r in results:
            fw  = r.get("framework", "")
            pct = r.get("coverage_percent", 0)
            if fw:
                aggregate.setdefault(fw, []).append(pct)

    return {
        fw: round(sum(scores) / len(scores), 1)
        for fw, scores in aggregate.items()
        if scores
    }