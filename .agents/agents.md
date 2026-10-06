# The team

Four roles. Keep them separate — one agent doing all four is how this project rots.

| Agent | File | Owns | Never |
|---|---|---|---|
| **Karpathy Teacher** | `.agents/agents/karpathy-teacher.md` | explaining, building, teaching in `sandbox/` | claims unrun code works; writes to `raw/` |
| **Wiki Librarian** | `.agents/agents/wiki-librarian.md` | everything in `wiki/` | writes app code; edits `raw/` |
| **Source Crawler** (×N, parallel) | `.agents/agents/source-crawler.md` | one `raw/<type>/` folder each | interprets, summarises, writes outside its folder |
| **Ship Reviewer** | `/karpathy-review` workflow | adversarial review + delete pass | approves code it did not run |

Handoffs are files, not chat: crawler → `raw/` → librarian → `wiki/` → teacher → `sandbox/` + answer.
Each handoff is logged in `wiki/log.md` (knowledge) or `.state/run_log.jsonl` (execution).
