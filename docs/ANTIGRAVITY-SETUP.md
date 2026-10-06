# Antigravity setup — step by step (aur Claude Code se kya alag hai)

Video Claude Code me bana hai. Antigravity me **ye setup actually behtar baithta hai**, sirf ek
cheez missing hai (hooks) jiska workaround is repo me already bana hua hai.

---

## 1. Claude Code → Antigravity mapping

| Video me (Claude Code) | Antigravity me | Is repo me file |
|---|---|---|
| `CLAUDE.md` (schema) | `AGENTS.md` ya `GEMINI.md` (root) — dono read hote hain | `AGENTS.md`, `GEMINI.md` |
| always-on instructions | **Rules** → `.agents/rules/*.md` (YAML frontmatter zaroori) | `.agents/rules/00..03` |
| slash command | **Workflow** → `.agents/workflows/<name>.md` → `/name` | 8 workflows |
| Skill (`SKILL.md`) | **Skill** → `.agents/skills/<name>/SKILL.md` | `karpathy-teach`, `wiki-graph` |
| Subagent | **Custom agent** → `.agents/agents/<name>.md` + frontmatter (`subagent: true`, `model`, `commandExecutionPolicy`) | 3 personas |
| Parallel subagents | **Agent Manager** (multiple agents side-by-side) | `/crawl-sources` |
| Stop **hook** (run gate) | ❌ nahi hai → script + always_on rule se enforce | `scripts/verify_gate.py` + rule 02 |
| — | **Artifacts / walkthroughs / browser tool** (video me nahi, Antigravity me bonus) | §5 |
| — | **Knowledge Items** (sessions ke beech memory) | §6 |

Key facts jo yaad rakho:

- Rules **recursive** hain: Antigravity file ke folder se workspace root tak chalta hai aur har
  level ki `AGENTS.md` / `GEMINI.md` / `.agents/rules/*.md` load karta hai.
- `.agents/rules/*.md` me frontmatter **compulsory** hai aur trigger valid hona chahiye
  (`always_on`, `model_decision`, glob). Galat/missing frontmatter = rule **chupchap ignore**
  ho jata hai. `camelCase` (`alwaysOn`) galat hai.
- `.agents/rules/` me sirf **immediate .md children** scan hote hain (subfolder nahi, jab tak
  `.agents/rules.json` me register na karo).
- Per-rule-file limit ~**12,000 characters**. Isiliye schema `AGENTS.md` me hai aur rules chhote
  chhote files me bante hain.
- Global rules: `~/.gemini/AGENTS.md` ya `~/.gemini/GEMINI.md` (sab projects me). Legacy
  `.agent/rules/` (bina `s`) abhi bhi kaam karta hai, par naya default `.agents/` hai.

---

## 2. Pehli baar chalane ke steps

```bash
# 1. is folder ko Antigravity me kholo (File > Open Folder)
# 2. python env
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# 3. secrets (optional)
cp .env.example .env    # TWITTERAPI_IO_KEY bharo agar X chahiye
```

Antigravity settings (bottom-right gear → Settings):

1. **Terminal Command Auto Execution** → shuru me `Request Review` rakho. Jab trust ban jaye
   tab `Always Proceed` + denylist.
2. **Agent Non-Workspace File Access** → **off** hi rehne do (default). Crawler ko workspace ke
   bahar likhne ki zarurat nahi.
3. **Customization → Rules** me check karo ki chaaron rules "active" dikh rahe hain. Na dikhein
   to frontmatter galat hai.
4. Chat me `/` dabao — `/crawl-sources`, `/build-wiki`, `/extract-rules`, `/karpathy-teach`,
   `/karpathy-ingest`, `/karpathy-review`, `/wiki-lint`, `/wiki-graph` dikhne chahiye.
5. `/agents` se dekho ki `karpathy-teacher`, `wiki-librarian`, `source-crawler` list me hain.

Phir `PROMPTS.md` ke Prompt 1 → 6 order me chalao.

---

## 3. Models ka division (credits bachane ke liye)

| Kaam | Model | Kyun |
|---|---|---|
| Crawling, file fetch, boilerplate | fast/flash | sirf I/O hai, soch nahi |
| Wiki compile, rules extract, teaching | pro / sabse strong | yahi actual compression aur reasoning hai |
| Lint, graph, manifest | fast/flash | deterministic scripts chalane hain |

Persona files me `model:` already set hai — apne plan ke hisaab se badal lena.

---

## 4. Run gate — hook ka Antigravity version (ye sabse important adaptation hai)

Claude Code me Stop hook turn ko block kar deta hai. Antigravity me aisa kuch nahi, isliye:

```bash
# code chalao hamesha isse (proof .state/run_log.jsonl me jata hai)
python scripts/run_and_log.py -- python sandbox/bpe.py

# turn khatam karne se pehle (jab bhi code likha/badla ho)
python scripts/verify_gate.py          # exit 0 = answer allowed, exit 1 = BLOCKED
```

Teen jagah isko bandha gaya hai taaki agent skip na kar sake:

1. `.agents/rules/02-verification-gate.md` — `always_on`, matlab har turn ke system prompt me.
2. Har code-producing workflow ka last step.
3. `karpathy-teacher` persona ki hard constraint.

Tested (is repo me chala ke dekha gaya):

```
$ python scripts/verify_gate.py
[gate] BLOCKED - do not claim this works yet.
  NEVER RUN SINCE LAST EDIT : sandbox/_gate_check.py
      python scripts/run_and_log.py -- python sandbox/_gate_check.py

$ python scripts/run_and_log.py -- python sandbox/_gate_check.py
hello from sandbox
[run_and_log] OK in 0.01s · logged to .state/run_log.jsonl

$ python scripts/verify_gate.py
[gate] PASS - 1 changed file(s) all have a post-edit run logged.
```

Extra sakhti chahiye? `python scripts/verify_gate.py --require-pass` (non-zero exit par bhi fail)
aur `--paths sandbox scripts` (jab tooling khud edit ki ho).

---

## 5. Antigravity ke 3 bonus jo video me nahi the

- **Browser tool** — graph ko khud khol ke **screenshot** le sakta hai, aur crawl verify kar sakta
  hai. `/wiki-graph` ka step 3 yahi hai: agent server start karta hai, page kholta hai, screenshot
  attach karta hai. Aapko file path nahi, **tasveer** milti hai.
- **Artifacts / walkthrough** — har bade task ke baad agent plan + walkthrough likhta hai. Use
  karo: `/build-wiki` ke end me bolo *"walkthrough me pages-per-folder table aur orphan list daalo"*.
- **Agent Manager (parallel agents)** — crawl me yahi 45 min wala kaam 10 min ka banata hai.
  Rule: **ek agent = ek folder**. Do agents ek hi folder me likhenge to file conflicts aur
  duplicate fetch milenge.

---

## 6. Knowledge Items (Antigravity ki apni memory) vs wiki

Antigravity har conversation ke baad Knowledge Items banata hai. Ye **replacement nahi** hai:

| | Knowledge Items | `wiki/` |
|---|---|---|
| Kaun likhta hai | Antigravity, automatically | aapka agent, deliberately |
| Kahan | app ka internal storage | aapke repo me, git me |
| Portable? | nahi | haan (Claude Code, Cursor, Obsidian sab padh lenge) |
| Quote-backed? | nahi | haan, warna rule violation |

Isliye `AGENTS.md` me likha hai: durable knowledge **wiki me** jati hai. KI ko project ki
chhoti-moti preferences ke liye chhod do.

---

## 7. Kya Antigravity ke liye ye sahi rahega? — seedha jawab

**Haan, 4 wajah se behtar:**

1. **Parallel crawl** Agent Manager me natively aasaan hai (video me yahi sabse slow step tha).
2. **Rules ka recursive, progressive-disclosure system** (`model_decision`) matlab 700k words wale
   project me context fulega nahi — agent sirf zarurat par rule/page kholta hai.
3. **Browser tool** se visual graph ka screenshot aur crawl verification agent khud kar leta hai.
4. Wiki markdown + git hai, to Antigravity, Claude Code, Cursor, Obsidian — sab ek hi brain par
   kaam karenge. Lock-in zero.

**Teen jagah dhyan rakhna:**

1. **Hook nahi hai** → gate convention-based hai. Agar agent ek-do baar skip kare, prompt me
   likho: *"last action: run verify_gate.py and paste its output"*. (Is repo me teen jagah
   enforce kiya gaya hai.)
2. **12k char rule limit + flat rules folder** → rules chhote rakho, lambi guidance wiki/docs me.
3. **Rules kabhi-kabhi ignore ho jate hain** (community ki common shikayat) → bade tasks me
   workflow (`/...`) se chalao, kyunki workflow trajectory-level hota hai, rule sirf
   prompt-level context.

**Cost reality check:** 700k words ek baar me context me nahi aate. Isliye `/build-wiki`
batches me chalta hai aur `log.md` me checkpoint karta hai — ye optional nahi hai.

---

## 8. Agar kuch kaam na kare

| Problem | Fix |
|---|---|
| `/` par workflow nahi dikh raha | file `.agents/workflows/` me ho, frontmatter me `description:` ho, folder root par ho |
| Rule apply nahi ho raha | `.agents/rules/*.md` me `trigger:` valid hai? subfolder me to nahi hai? 12k se bada to nahi? |
| Agent `raw/` edit kar raha hai | rule 00 ko prompt me dobara yaad dilao; `/wiki-lint` chala ke damage dekho; git se revert karo |
| Graph khali | pehle `/build-wiki` chalao; ya `python scripts/build_graph.py --min-degree 0` |
| Crawl 403/429 de raha | `--sleep 2` badhao; paywall wale sources `raw/misc/` me manually clip karo |
| Gate hamesha BLOCKED | `.state/` exists? code `sandbox/` me likha ja raha hai? `--window` badhao |
