# PROMPTS — Antigravity ko dene wale copy-paste prompts

Video (Nate Herk, *I Built Another Andrej Karpathy Using Claude*) me 6 prompts **screen par dikhaye
gaye the, bole nahi gaye** — isliye unka verbatim text public transcript me nahi hai.
Niche ke prompts us video me batayi gayi **exact functionality** se reconstruct kiye gaye hain
(crawl → wiki → rules → agent+skill → run gate → test), aur Claude Code ki jagah **Antigravity ke
primitives** (Rules / Workflows / Skills / custom agents / Agent Manager) ke liye likhe gaye hain.

> Order matters. Ek prompt chalao, output verify karo, phir next. Beech me `/wiki-lint` aur
> `/wiki-graph` chalate raho.

---

## Prompt 0 — Scaffold (ye poora folder structure khud bana dega)

> Isi repo me ye sab already bana hua hai. Prompt 0 tab use karo jab **naye project** me
> (ya kisi aur expert ke liye) zero se banana ho.

```
You are setting up an "expert brain" workspace in Antigravity, based on Andrej Karpathy's
LLM Wiki pattern (gist: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

Create exactly this structure in the current workspace, nothing extra:

AGENTS.md                      # schema: 3 layers, page format, ingest/query/lint ops, run gate
GEMINI.md                      # one-liner that @-includes AGENTS.md
.agents/rules/00-wiki-schema.md            # trigger: always_on
.agents/rules/01-karpathy-operating-rules.md  # trigger: always_on (placeholder 7 rules for now)
.agents/rules/02-verification-gate.md      # trigger: always_on
.agents/rules/03-crawl-and-sources.md      # trigger: model_decision
.agents/workflows/{crawl-sources,build-wiki,extract-rules,karpathy-teach,karpathy-ingest,karpathy-review,wiki-lint,wiki-graph}.md
.agents/skills/karpathy-teach/SKILL.md
.agents/skills/wiki-graph/SKILL.md
.agents/agents/{karpathy-teacher,wiki-librarian,source-crawler}.md   # YAML frontmatter personas
.agents/agents.md              # the team table + handoff contract
scripts/{crawl_youtube,crawl_web,crawl_x,crawl_report,build_graph,wiki_lint,run_and_log,verify_gate}.py
config/sources.json            # the crawl manifest
raw/{youtube,blog,github,x,papers,misc}/  + raw/README.md   # IMMUTABLE
wiki/{index.md,log.md,overview.md,sources/,topics/,principles/,rules/,methods/,people/,_graph/}
sandbox/  .state/  requirements.txt  .env.example  .gitignore

Hard constraints to encode in AGENTS.md and the rules:
- raw/ is immutable; wiki/ is agent-owned; every claim needs a verbatim quote + source link,
  otherwise it must be labelled "INFERRED".
- Every rule file in .agents/rules/ starts with YAML frontmatter (`trigger: always_on` or
  `model_decision` + `description:`) and stays under 12,000 characters.
- Wiki pages: YAML frontmatter (title, type, tags, sources, confidence, last_updated),
  one-paragraph summary, Evidence section with quotes, Related backlinks via [[wiki-links]].
- index.md updated and log.md appended on EVERY wiki mutation
  (format: `## [YYYY-MM-DD] <op> | <title>`).
- Antigravity has no Stop hook, so the run gate is scripts/verify_gate.py, which the agent must
  call as its last action in any turn that touched code. scripts/run_and_log.py records proof.

Scripts must be pure stdlib except the crawlers (youtube-transcript-api, yt-dlp, trafilatura,
markdownify). Write them, run each one's --help, and show me the tree when you're done.
Do not crawl anything yet.
```

---

## Prompt 1 — Crawl (sab kuch `raw/` me, parallel subagents)

```
Fill raw/ with Andrej Karpathy's public material. Read config/sources.json first; add anything
obviously missing (his blogs, the Zero-to-Hero playlist, his teaching repos, his X posts).

Rules of engagement:
- One subagent PER SOURCE TYPE, running in parallel via the Agent Manager:
  youtube | blog | github | x | papers. Each subagent owns exactly one raw/<type>/ folder and
  writes nowhere else. Use .agents/agents/source-crawler.md as the persona.
- Tools: scripts/crawl_youtube.py (youtube-transcript-api, yt-dlp fallback),
  scripts/crawl_web.py (trafilatura), scripts/crawl_x.py (twitterapi.io, key in .env).
  Setup first: python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
- Verbatim capture only. No summarising at this stage. YAML frontmatter on every file
  (title, url, date, source_type, word_count, fetched_at). Skip files that already exist.
- Rate limit 1 req/sec, 3 retries. Public content only. Nothing behind a login or paywall —
  list those for me to clip manually instead.
- No TWITTERAPI_IO_KEY? Skip X, write the gap into raw/x/_GAP.md, carry on.

When all subagents finish: run python scripts/crawl_report.py and show me raw/MANIFEST.md —
files and word counts per source type, date range, and every failure with its reason.
Then STOP and wait for my go-ahead. Target: 500k+ words. Expect 30-60 minutes.
```

---

## Prompt 2 — Wiki compile (gist paste karke)

```
<<< PASTE THE FULL TEXT OF https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f HERE >>>

Apply exactly this pattern to this workspace:
- raw/ = the immutable sources layer (never modify it)
- wiki/ = the compiled layer that you own
- AGENTS.md = the schema; update it if this gist suggests a better convention

Compile everything in raw/ into wiki/, in passes, following .agents/workflows/build-wiki.md:
1. one wiki/sources/<date>-<slug>.md per raw artifact (150-word summary + 3-8 verbatim
   pull-quotes with timestamps/anchors + topics touched + link to the raw path)
2. wiki/topics/ and wiki/people/ for anything appearing in 2+ sources
3. wiki/principles/ (durable beliefs) and wiki/methods/ (how-he-explains, how-he-debugs,
   how-he-builds, how-he-teaches, how-he-uses-llms) — this layer is what makes the agent THINK
   like him instead of just quoting him
4. wiki/overview.md: the 10 things that matter most, with links, plus every contradiction you
   found (do not smooth them over)
5. wiring pass: bidirectional [[links]], full index.md grouped by folder, log.md appended

Checkpoint to log.md after every batch of 10 sources so a crash doesn't lose progress.
Finish with: python scripts/wiki_lint.py  (fix until 0 errors) and /wiki-graph.
Then show me: page counts per folder, the 5 biggest hubs, and the orphans.
```

---

## Prompt 3 — Rules extract (har rule ke peeche exact quote)

```
Run /extract-rules.

Read wiki/methods/, wiki/principles/ and every source page tagged teaching/debugging/workflow/
llm-usage. Find the behaviours that repeat across 3+ INDEPENDENT sources — the way he works,
not the topics he knows. Aim for ~7 rules (merge anything that splits hairs).

For each rule write wiki/rules/<slug>.md with:
- 1-3 VERBATIM quotes, each with a [[sources/...]] link and a timestamp/anchor
- confidence: high (2+ independent sources) / medium (1) / inferred (0)
- "What this looks like in practice": 3 concrete agent behaviours
- "Failure mode it prevents": one line

Absolute rule: never invent a quote. If you believe a rule but cannot quote it, put it under
"## Inferred" and say so. A missing quote is a finding, not a problem to hide.

Then rewrite .agents/rules/01-karpathy-operating-rules.md from these pages (keep it under
12,000 chars) and show me a table: rule | confidence | #sources | strongest quote.
I will sign off before you continue.
```

---

## Prompt 4 — Agent + Skill (mini Karpathy)

```
Turn the rules into two Antigravity artifacts:

1. A custom subagent at .agents/agents/karpathy-teacher.md with YAML frontmatter
   (name, description, subagent: true, mainAgent: true, model: pro,
    commandExecutionPolicy: sandbox, inheritMcp: false).
   Body = the 7 rules as behaviour, the per-task loop
   (smallest version -> predict -> run -> compare -> add one thing), hard constraints
   (no claim without a logged run; no quote without a source; code only in sandbox/),
   tone (direct, no filler, no praise, no emoji), and the mandatory closing recap table:
   what I ran | what came out | what I changed | which rule drove each move.

2. A skill at .agents/skills/karpathy-teach/SKILL.md + a workflow at
   .agents/workflows/karpathy-teach.md so that `/karpathy-teach <topic>` routes the task to that
   subagent, and then SELF-GRADES the answer against a checklist — one line per rule,
   PASS/WEAK/FAIL/N/A with a reason. Any FAIL must be fixed before the answer is shown to me.

Also add /karpathy-ingest (one link in -> ripple through 5-15 wiki pages) and /karpathy-review
(adversarial "would it ship?" pass). Show me the file tree and the frontmatter of each new file.
```

---

## Prompt 5 — Run gate (Claude Code ke hook ka Antigravity version)

```
Antigravity has no Stop hook, so build the gate in-repo and make it unskippable by convention:

1. scripts/run_and_log.py — wrapper: runs any command, streams output, appends
   {ts, cmd, tag, exit_code, duration_s, files, stdout, stderr} to .state/run_log.jsonl.
2. scripts/verify_gate.py — scans sandbox/ for code files modified in the last N minutes and
   fails (exit 1) unless run_log.jsonl has a run referencing that file AT OR AFTER its mtime.
   Prints the exact command to fix each violation. --require-pass also fails on non-zero runs.
3. .agents/rules/02-verification-gate.md (trigger: always_on) — states: execute only via
   run_and_log.py; call verify_gate.py as the LAST action of any turn that touched code;
   never write "this works" without pasted real output; if execution is impossible, mark the
   code **UNVERIFIED** and give me the exact command to run.
4. Add the gate step to every workflow that can produce code.

Prove it works: create a throwaway sandbox file, show the gate BLOCKING (exit 1), run the file
through run_and_log.py, show the gate PASSING (exit 0), paste both outputs, then delete the file.
Also set Antigravity's Terminal Command Auto Execution to "Request Review" while we test this.
```

---

## Prompt 6 — Test it on something real

```
Three tests, one after the other. Follow .agents/rules/01-karpathy-operating-rules.md exactly.

A) /karpathy-teach build a byte-pair encoding tokenizer and teach me how it works
   Expected shape: assumptions -> what "done" means -> smallest version that runs on a tiny
   input -> your PREDICTION before running -> real output -> did it hold -> the broken version
   and why it breaks -> fix -> recap table -> rule self-grade.

B) /karpathy-review sandbox/<the script you just wrote>
   Predict 3-5 concrete failure modes BEFORE running (emoji on a cp1252 Windows terminal,
   empty input, 10k items, 429s, paths with spaces). Reproduce each one for real:
   PYTHONIOENCODING=cp1252 python scripts/run_and_log.py -- python <file>
   Then do the delete pass, and PROVE the trimmed version matches the original by running both
   on the same input and diffing the output. Verdict table at the end.

C) /karpathy-ingest <a fresh Karpathy link that is not in raw/ yet>
   Show me the ripple: pages created, pages updated, any rule promoted from medium to high
   because it just got its second independent source, and the log.md entry.
   Then /wiki-graph and tell me what changed in the shape of the brain.
```

---

## Daily loop (build ke baad)

| Kab | Command |
|---|---|
| Kuch samajhna/banana ho | `/karpathy-teach <topic>` |
| Naya link mila | `/karpathy-ingest <url>` |
| Client/prod ko bhejne se pehle | `/karpathy-review <path>` |
| Har ~10 ingest ke baad | `/wiki-lint` phir `/wiki-graph` |
| Status check / kisi ko dikhana ho | `/dashboard` |
| Mahine me ek baar | `/extract-rules` dobara — dekho kaunsa rule promote hua |

## Kisi aur expert ke liye reuse

`config/sources.json` badlo, `.agents/rules/01-*.md` ko naye rules se overwrite karne do,
agent persona ka naam badlo. Baaki poora pipeline same rehta hai — yahi video ka main point hai.
