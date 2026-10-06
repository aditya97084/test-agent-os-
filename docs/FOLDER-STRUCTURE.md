# Folder structure — kya, kahan, aur kyun

Sabse pehle folder structure hi decide karna sahi hai (jaisa aapne kaha) — kyunki is pattern me
**folder structure hi schema hai**. Agent ko kaunsi file kahan likhni hai, ye hi uska contract hai.

---

## Poora tree

```
test-agent-os-/                     ← Antigravity me YAHI folder kholna hai (workspace root)
│
├── AGENTS.md                       ← schema. 3 layers, page format, operations, run gate.
├── GEMINI.md                       ← Antigravity ka native naam; @AGENTS.md include karta hai
├── PROMPTS.md                      ← 6 copy-paste prompts (+ Prompt 0 = scaffold)
├── requirements.txt                ← sirf crawlers ke liye; baaki sab stdlib
├── .env.example → .env             ← TWITTERAPI_IO_KEY (gitignored)
├── .gitignore
│
├── .agents/                        ← Antigravity ka native config folder
│   ├── agents.md                   ← team table + handoff contract
│   ├── agents/                     ← personas (YAML frontmatter wale custom agents)
│   │   ├── karpathy-teacher.md     ← mini-Karpathy (mainAgent + subagent)
│   │   ├── wiki-librarian.md       ← sirf wiki/ maintain karta hai
│   │   └── source-crawler.md       ← ek instance per raw/<type>/ folder
│   ├── rules/                      ← always-on constraints (har file me frontmatter MUST)
│   │   ├── 00-wiki-schema.md       ← raw immutable, wiki agent-owned, quote-or-INFERRED
│   │   ├── 01-karpathy-operating-rules.md  ← 7 rules (extract-rules isko overwrite karega)
│   │   ├── 02-verification-gate.md ← run-before-you-answer
│   │   └── 03-crawl-and-sources.md ← model_decision: sirf crawl ke waqt load hota hai
│   ├── skills/                     ← on-demand capabilities
│   │   ├── karpathy-teach/SKILL.md
│   │   └── wiki-graph/SKILL.md
│   └── workflows/                  ← slash commands
│       ├── crawl-sources.md        /crawl-sources     (step 1)
│       ├── build-wiki.md           /build-wiki        (step 2)
│       ├── extract-rules.md        /extract-rules     (step 3)
│       ├── karpathy-teach.md       /karpathy-teach    (daily)
│       ├── karpathy-ingest.md      /karpathy-ingest   (daily)
│       ├── karpathy-review.md      /karpathy-review   (ship se pehle)
│       ├── wiki-lint.md            /wiki-lint         (har ~10 ingest)
│       └── wiki-graph.md           /wiki-graph        (visual)
│
├── config/sources.json             ← crawl manifest: kaunsa source, kaunse tool se, kyun
│
├── raw/                            ← LAYER 1 — IMMUTABLE (agent padhta hai, chhuta nahi)
│   ├── youtube/                    ← timestamped captions, 1 file per video
│   ├── blog/                       ← posts → markdown
│   ├── github/                     ← READMEs
│   ├── x/                          ← posts, 1 file per year
│   ├── papers/  misc/              ← pdfs, manual clips (Obsidian Web Clipper)
│   ├── README.md
│   └── MANIFEST.md                 ← generated: files/words per type, failures, gaps
│
├── wiki/                           ← LAYER 2 — agent ki property (aap sirf padhte ho)
│   ├── index.md                    ← master catalog — HAR page yahan listed hona chahiye
│   ├── log.md                      ← append-only: ## [YYYY-MM-DD] op | title
│   ├── overview.md                 ← top-10 synthesis + open contradictions
│   ├── sources/                    ← 1 page per ingested artifact (summary + pull-quotes)
│   ├── topics/                     ← wo kya jaanta hai (tokenization, RL, scaling…)
│   ├── principles/                 ← durable beliefs
│   ├── rules/                      ← 7 operating rules, har ek quote-backed + confidence
│   ├── methods/                    ← how he explains / debugs / builds / teaches / uses LLMs
│   ├── people/                     ← orgs, projects, collaborators
│   └── _graph/                     ← generated: graph.html, graph.json, graph.md, lint-report.md
│
├── scripts/                        ← tooling (crawlers ke alawa sab pure stdlib)
│   ├── crawl_youtube.py            youtube-transcript-api → yt-dlp fallback
│   ├── crawl_web.py                trafilatura → markdownify → crude strip
│   ├── crawl_x.py                  twitterapi.io (key nahi? gap note likh ke clean exit)
│   ├── crawl_report.py             → raw/MANIFEST.md
│   ├── build_graph.py              → wiki/_graph/graph.{html,json,md} + hubs/orphans/weak rules
│   ├── wiki_lint.py                broken links, orphans, unquoted rules, stale, index gaps
│   ├── run_and_log.py              har run ka proof → .state/run_log.jsonl
│   └── verify_gate.py              RUN GATE: unrun code par exit 1
│
├── sandbox/                        ← LAYER 3 — teaching ke time ka chalne wala code
└── .state/run_log.jsonl            ← execution proof (gitignored)
```

---

## Design decisions (kyun aise)

1. **`.agents/` root par hai, `wiki/` ke andar nahi.** Antigravity rules ko file ke folder se
   root tak walk karke load karta hai — config root par rakhne se har agent ko same contract
   milta hai.
2. **`raw/` aur `wiki/` sibling hain, nested nahi.** "Immutable" ka matlab path-level separation
   hona chahiye, sirf instruction nahi. Rule 00 bolta hai, aur directory layout usko obvious
   banata hai.
3. **`wiki/` ke andar type-folders** (`rules/ topics/ methods/ ...`) — isse graph me colour aur
   cluster automatically mil jate hain, frontmatter galat ho tab bhi folder se type infer hota hai.
4. **`sandbox/` alag hai** taaki run gate ka scope chhota rahe: teaching code policed hai,
   tooling nahi (jab tak `--paths scripts` na do).
5. **`.state/` gitignored** — execution proof session ka hai, repo ka nahi.
6. **`raw/**` gitignored** — third-party content + size. Jo artifact commit hota hai wo `wiki/`
   hai (Karpathy: "the wiki is just a git repo of markdown files").
7. **`config/sources.json`** alag file hai taaki kisi aur expert ke liye reuse karte waqt sirf
   yahi badalna pade.

---

## Naming conventions

| Cheez | Format | Example |
|---|---|---|
| Source page | `YYYY-MM-DD-slug.md` | `wiki/sources/2024-02-lets-build-the-gpt-tokenizer.md` |
| Rule page | verb-first kebab | `wiki/rules/predict-then-run-then-compare.md` |
| Method page | `how-he-<verb>.md` | `wiki/methods/how-he-debugs.md` |
| raw YouTube | `YYYY-MM-DD-title-<videoid>.md` | `raw/youtube/2024-02-20-lets-build-...-zduSFxRajkE.md` |
| raw X | `YYYY-posts-<user>.md` | `raw/x/2026-posts-karpathy.md` |
| Log entry | `## [YYYY-MM-DD] op \| title` | grep-able: `grep "^## \[" wiki/log.md \| tail -5` |

## Kisi aur expert ke liye

Sirf 3 cheezein badlo: `config/sources.json`, persona ka naam/description
(`.agents/agents/karpathy-teacher.md`), aur `.agents/rules/01-*.md` (jo `/extract-rules` khud
overwrite kar dega). Folder structure, scripts, gate, graph — sab waise ka waisa chalega.
