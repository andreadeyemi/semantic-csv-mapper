# semantic-csv-mapper  
**Heuristic-first, LLM-enhanced CSV normalization for SaaS onboarding & analytics.**  
Turn any messy customer export into a clean, typed schema + SQLite table in **seconds**.

![Python](https://img.shields.io/badge/Python-3.10%2B-informational)
![Design](https://img.shields.io/badge/Design-Deterministic%20%2B%20AI-success)
![License](https://img.shields.io/badge/License-MIT-blue)

> **Why this exists**  
> Data onboarding should be instant. This tool auto-labels columns (email, company, MRR, churnFlag, createdAt, etc.), cleans types, and emits both a **normalized CSV** and a **SQLite** table you can query immediately.  
> Works offline via fast heuristics; upgrades with an LLM when you provide an API key.

---

## 🔥 Features
- **Semantic labeling**: robust regex + value hints; optional LLM for ambiguity.
- **Type normalization**: dates → `datetime`, currency → `float`, booleans → `True/False`.
- **Schema standardization**: consistent, analytics-ready headers.
- **Dual output**: `clean.csv` + `clean.db` (`customers` table).
- **Deterministic first**: identical inputs → identical outputs; LLM only when asked.

**Canonical fields**
uuid, email, fullName, firstName, lastName, company, domain,
plan, mrr, arr, nps, churnFlag, createdAt, lastSeen,
phone, country, state, city, zip, notes, other

---

## ⚡ Quickstart
```bash
pip install -r requirements.txt
# Optional AI boost:
# export OPENAI_API_KEY=sk-...

python main.py --in examples/sample_customers.csv --out clean.csv --sqlite clean.db

Outputs

clean.csv — standardized headers + typed values

clean.db — SQLite database with table customers
🎯 Example

Input (messy)

E-mail,Full Name,Company,Monthly Recurring ($),Plan,Active?,Signed Up,Last Login
jane@acme.co,Jane Redd,Acme Inc,$129,Pro,yes,2025-08-01,2025-09-20


Terminal report

=== Semantic Mapping Report ===
E-mail                  → email      | matched pattern email|e-?mail
Full Name               → fullName   | matched pattern ^name$|full[_\s-]?name
Company                 → company    | matched pattern company|account|org(anization)?
Monthly Recurring ($)   → mrr        | value hint currency
Plan                    → plan       | matched pattern plan|tier|package
Active?                 → churnFlag  | value hint boolean
Signed Up               → createdAt  | value hint date
Last Login              → lastSeen   | matched pattern last[_\s-]?login|activity

Saved: clean.csv
SQLite: clean.db (table: customers)


Output (clean.csv)

email,fullName,company,mrr,plan,churnFlag,createdAt,lastSeen
jane@acme.co,Jane Redd,Acme Inc,129.0,Pro,False,2025-08-01,2025-09-20 00:00:00

🧠 How it works

Heuristic pass: Column name patterns + sample value hints assign labels.

LLM pass (optional): Ambiguous columns get a label with rationale.

Normalizer: Types are enforced (dates, currency, booleans).

Emitter: Writes ordered columns to CSV + SQLite.

Deterministic: if no API key is provided, results are fully reproducible.

🛠️ CLI

usage: main.py --in <path.csv> --out <clean.csv> [--sqlite <clean.db>]


--in path to source CSV

--out path for cleaned CSV

--sqlite (optional) also write SQLite DB with table customers

🔒 Security

Processes data in-memory only.

No network calls unless you export OPENAI_API_KEY.

Keep keys in env vars or .env; never commit secrets.

🧪 Minimal test
python main.py --in examples/sample_customers.csv --out /tmp/out.csv
python - <<'PY'
import pandas as pd
df = pd.read_csv("/tmp/out.csv")
assert set(["email","company","mrr","createdAt"]).issubset(df.columns)
print("✅ schema sanity OK")
PY

📈 Roadmap

--report md → quick profiling (nulls, top domains, churn %)

Pluggable schema profiles (Salesforce, HubSpot, custom)

Streaming mode for very large CSVs

🤝 Contributing

Issues and PRs welcome. Keep diffs small, deterministic, and tested.

📜 License

MIT © 2025 André Adeyemi
