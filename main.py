import argparse, os, re, json
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv

# Optional: use OpenAI to label ambiguous columns
def llm_label(column_name, sample_values, api_key=None):
    if not api_key:
        return None, None
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    prompt = f"""
Map the column '{column_name}' with example values {sample_values[:5]} 
to one of these fields (or 'other'):
['email','fullName','firstName','lastName','company','domain','mrr','arr',
 'plan','nps','churnFlag','createdAt','lastSeen','phone','country','state',
 'city','zip','uuid','notes','other'].
Return JSON like {{ "label": "...", "reason": "..." }} only.
"""
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )
        data = json.loads(resp.choices[0].message.content)
        return data.get("label"), data.get("reason")
    except Exception:
        return None, None

# Heuristic patterns for instant mapping
PATTERNS = [
    ("email", re.compile(r"email|e-?mail", re.I)),
    ("fullName", re.compile(r"^name$|full[_\s-]?name", re.I)),
    ("firstName", re.compile(r"^first[_\s-]?name|^fname$", re.I)),
    ("lastName", re.compile(r"^last[_\s-]?name|^lname$", re.I)),
    ("company", re.compile(r"company|account|org(anization)?", re.I)),
    ("domain", re.compile(r"domain|website|url", re.I)),
    ("mrr", re.compile(r"\bmrr\b|monthly[-_\s]?recurring", re.I)),
    ("arr", re.compile(r"\barr\b|annual[-_\s]?recurring", re.I)),
    ("plan", re.compile(r"plan|tier|package", re.I)),
    ("nps", re.compile(r"\bnps\b|net promoter", re.I)),
    ("churnFlag", re.compile(r"churn|cancel", re.I)),
    ("createdAt", re.compile(r"created|signup|joined|start", re.I)),
    ("lastSeen", re.compile(r"last[_\s-]?seen|last[_\s-]?login|activity", re.I)),
    ("phone", re.compile(r"phone|mobile|cell", re.I)),
    ("country", re.compile(r"country", re.I)),
    ("state", re.compile(r"state|province|region", re.I)),
    ("city", re.compile(r"city|town", re.I)),
    ("zip", re.compile(r"zip|postal", re.I)),
    ("uuid", re.compile(r"uuid|id$|guid", re.I)),
    ("notes", re.compile(r"notes?|comments?", re.I)),
]

STANDARD_ORDER = [
    "uuid","email","fullName","firstName","lastName","company","domain",
    "plan","mrr","arr","nps","churnFlag",
    "createdAt","lastSeen","phone","country","state","city","zip","notes","other"
]

def guess_label(name, series):
    for label, pat in PATTERNS:
        if pat.search(name):
            return label, f"matched pattern {pat.pattern}"
    sample = series.dropna().astype(str).head(20).tolist()
    if any("@" in v for v in sample):
        return "email", "value hint '@'"
    if any(re.search(r"\$\s?\d|\d+\.\d{2}", v) for v in sample):
        return "mrr", "value hint currency"
    if any(re.search(r"\d{4}-\d{2}-\d{2}", v) for v in sample):
        return "createdAt", "value hint date"
    return None, None

def normalize(label, series):
    s = series.copy()
    if label in ("mrr","arr"):
        s = s.astype(str).str.replace(r"[^\d.]", "", regex=True).replace("", "0").astype(float)
    elif label == "churnFlag":
        s = s.astype(str).str.lower().map(
            {"true":True,"yes":True,"1":True,"cancel":True,
             "false":False,"no":False,"0":False,"active":False}
        ).fillna(False)
    elif label in ("createdAt","lastSeen"):
        def _p(x):
            for fmt in ("%Y-%m-%d","%m/%d/%Y","%Y-%m-%d %H:%M:%S"):
                try: return datetime.strptime(str(x), fmt)
                except: pass
            return pd.NaT
        s = s.apply(_p)
    return s

def main():
    load_dotenv()
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="inp", required=True)
    p.add_argument("--out", dest="out", required=True)
    p.add_argument("--sqlite", dest="sqlite", default=None)
    args = p.parse_args()

    df = pd.read_csv(args.inp)
    api_key = os.getenv("OPENAI_API_KEY")
    mapping, report = {}, []

    for col in df.columns:
        label, reason = guess_label(col, df[col])
        if not label and api_key:
            ll, rr = llm_label(col, df[col].astype(str).dropna().tolist(), api_key)
            label, reason = ll or "other", rr or "LLM fallback"
        if not label: label, reason = "other", "no match"
        # ensure unique
        base = label; i = 2
        while label in mapping.values():
            label = f"{base}_{i}"; i += 1
        mapping[col] = label
        report.append((col, label, reason))

    clean = pd.DataFrame()
    for src, dst in mapping.items():
        clean[dst] = normalize(dst, df[src])

    order = [c for c in STANDARD_ORDER if c in clean.columns] + \
            [c for c in clean.columns if c not in STANDARD_ORDER]
    clean = clean[order]

    clean.to_csv(args.out, index=False)
    if args.sqlite:
        import sqlite3
        conn = sqlite3.connect(args.sqlite)
        clean.to_sql("customers", conn, if_exists="replace", index=False)
        conn.close()

    print("\n=== Semantic Mapping Report ===")
    for s, d, r in report:
        print(f"{s} → {d} | {r}")
    print(f"\nSaved: {args.out}")
    if args.sqlite:
        print(f"SQLite: {args.sqlite} (table: customers)")

if __name__ == "__main__":
    main()
