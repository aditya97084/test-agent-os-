# Karpathy Brain — Antigravity edition

Aapke bheje video ([I Built Another Andrej Karpathy Using Claude](https://www.youtube.com/watch?v=bvGptCLDhyo),
Nate Herk, 5 Oct 2026) ka poora setup — **Claude Code ki jagah Google Antigravity ke liye**,
ready-to-run form me. Video ki transcript padhi gayi hai, Karpathy ka original gist bhi, aur
yahan sab kuch **files me** bana diya gaya hai taaki Antigravity khud aage ka kaam kar le.

---

## TL;DR — aapke 5 sawaal, seedhe jawab

| Sawaal | Jawab | Detail |
|---|---|---|
| Video me hai kya? | Karpathy ke 700k+ words → wiki → uske 7 rules → ek agent + skill → run gate. 4 steps, 6 prompts. | [`docs/VIDEO-NOTES.md`](docs/VIDEO-NOTES.md) |
| Karpathy ka wo link? | **LLM Wiki gist** → https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f (4 Apr 2026) | [`docs/VIDEO-NOTES.md#5`](docs/VIDEO-NOTES.md) |
| Prompts kya the? | Video me sirf **screen par** dikhe the (bole nahi) → reconstruct karke Antigravity ke liye likh diye | [`PROMPTS.md`](PROMPTS.md) |
| Folder structure? | `raw/` (immutable) + `wiki/` (agent-owned) + `.agents/` (rules/workflows/skills/agents) + `scripts/` + `sandbox/` | [`docs/FOLDER-STRUCTURE.md`](docs/FOLDER-STRUCTURE.md) |
| Wo visual graph? | Obsidian graph view **ya** repo ka apna `/wiki-graph` (html + json + mermaid) | [`docs/VISUAL-GRAPH.md`](docs/VISUAL-GRAPH.md) |
| Antigravity ke liye sahi hai? | **Haan**, 4 jagah behtar — bas hooks nahi hain, uska workaround bana diya | [`docs/ANTIGRAVITY-SETUP.md#7`](docs/ANTIGRAVITY-SETUP.md) |

---

## Idea ek line me

Karpathy ka clone nahi — uske **public material ko ek wiki me compile** karke, usme se uske
**kaam karne ke rules** nikaal ke, ek aisa agent banana jo **uske tareeke se** sikhata aur banata
hai: sabse chhota chalne wala version pehle, run se pehle prediction, bina chalaye kabhi
"ye kaam karta hai" nahi.

> "You can outsource your thinking, but you cannot outsource your understanding." — video ki
> closing line

---

## Abhi kya ready hai

```
AGENTS.md + GEMINI.md        schema (Antigravity ise automatically rules ki tarah padhta hai)
.agents/rules/     4 rules   wiki invariants · 7 operating rules · run gate · crawl policy
.agents/workflows/ 8 commands /crawl-sources /build-wiki /extract-rules /karpathy-teach
                              /karpathy-ingest /karpathy-review /wiki-lint /wiki-graph
.agents/skills/    2 skills   karpathy-teach · wiki-graph
.agents/agents/    3 personas karpathy-teacher · wiki-librarian · source-crawler
scripts/           8 scripts  3 crawlers + manifest + graph + lint + run-logger + run-gate
config/sources.json           crawl manifest (edit karke apne sources daalo)
raw/ wiki/ sandbox/ .state/   teen layers + execution proof
PROMPTS.md                    Prompt 0-6, copy-paste ready
```

Scripts likh ke **chala ke test** kiye gaye hain (graph, lint, run-logger, gate — teen me se
teen pass). Crawlers ko network chahiye, isliye wo aapke machine par pehli baar chalenge.

---

## Start kaise karein (10 minute)

```bash
# 1) Antigravity me ye folder kholo (workspace root yahi hona chahiye)
python3 -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # X chahiye to TWITTERAPI_IO_KEY bharo (optional)

# 2) settings: Terminal Command Auto Execution = Request Review
#    Customization > Rules me chaaron rules active dikhne chahiye
#    chat me "/" dabao -> 8 workflows dikhne chahiye
```

Phir `PROMPTS.md` kholo aur **order me** chalao:

| # | Prompt | Kya hoga | Time |
|---|---|---|---|
| 1 | Crawl | parallel subagents `raw/` bharenge + `raw/MANIFEST.md` | 30-60 min |
| 2 | Wiki compile (gist paste) | `wiki/` ban jayegi, interlinked | 20-40 min |
| 3 | Rules extract | 7 rules, har ek ke peeche exact quote | 10 min |
| 4 | Agent + Skill | mini-Karpathy + `/karpathy-teach` self-grading | 5 min |
| 5 | Run gate | gate ko BLOCK aur PASS dono karte hue prove karega | 5 min |
| 6 | Test | BPE tokenizer teach + ship review + ek ingest | 15 min |

Har prompt ke baad **verify karo** (manifest padho, lint chalao, graph dekho) — tabhi next par jao.

---

## Roz ka use

```
/karpathy-teach  <jis cheez par atke ho>      # samajhna / banana
/karpathy-ingest <naya link>                  # brain ko behtar karo (1 link = 5-15 pages update)
/karpathy-review <file ya diff>               # "would it ship?" — delete-happy, run-first review
/wiki-lint                                     # har ~10 ingest ke baad
/wiki-graph                                    # shakal dekho: hubs, orphans, weak rules
```

---

## Jo cheez is setup ko "sach" rakhti hai

1. **Quote-or-INFERRED** — har claim ke peeche verbatim quote + source link, warna page par
   saaf likha hoga `INFERRED`. Quote banana (hallucinate) strictly band hai.
2. **Run gate** — `scripts/verify_gate.py` bina chale hue code par **exit 1** deta hai.
   Claude Code ka hook Antigravity me nahi hai, isliye ye script + always-on rule + har workflow
   ka last step — teen jagah se bandha hua hai.
3. **confidence field** — jis rule ke peeche 1 hi source hai wo `medium` ("bench par") rehta hai;
   doosra independent source milte hi `high` ho jata hai aur log me promotion likha jata hai.
4. **log.md + MANIFEST.md** — aap agent ka kaam bina 700k words padhe audit kar sakte ho.

---

## Niyam jo mat todna

- `raw/` kabhi edit mat karne dena — wahi poore system ka source of truth hai.
- Agent ko first person me "main Karpathy hoon" mat bolne dena. Ye uske **tareeke** ki copy hai,
  uski identity ki nahi. Personal/research use rakho; uske naam se public product mat banao.
- Wiki ko haath se mat likho. Aapka kaam: sources chunna, sawaal poochna, verify karna.

## Aage padho

- [`docs/VIDEO-NOTES.md`](docs/VIDEO-NOTES.md) — video ka full breakdown, 7 rules, gist ka saar, fact-check
- [`PROMPTS.md`](PROMPTS.md) — Prompt 0 (scaffold) se Prompt 6 (test) tak
- [`docs/FOLDER-STRUCTURE.md`](docs/FOLDER-STRUCTURE.md) — har folder kyun hai + naming rules
- [`docs/ANTIGRAVITY-SETUP.md`](docs/ANTIGRAVITY-SETUP.md) — Claude Code → Antigravity mapping, settings, troubleshooting
- [`docs/VISUAL-GRAPH.md`](docs/VISUAL-GRAPH.md) — graph banana aur **padhna**
