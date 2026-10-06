# Video me kya-kya hai (full breakdown) + Karpathy ke actual links

**Video:** [I Built Another Andrej Karpathy Using Claude](https://www.youtube.com/watch?v=bvGptCLDhyo)
— Nate Herk | AI Automation · 5 Oct 2026 · 10:45 · ~48k views
(aapka link: `https://youtu.be/bvGptCLDhyo?si=McHqzxJEq_j1S8si` — same video)

Maine poori transcript padh li hai. Niche jo bhi quote hai wo video ki transcript se hai,
aur jo links hain wo verify kiye gaye hain.

---

## 1. Video ka one-line idea

Karpathy ka voice clone nahi banaya — uske **700,000+ words** (lectures + blogs + repos + X posts)
ko ek wiki me compile karke, usme se uske **7 working rules** nikaal ke, ek Claude Code agent banaya
jo **uske tareeke se sochta aur sikhata hai**.

> "It's not a voice clone... It's an agent that condenses the way the best AI teacher, Andrej
> Karpathy, explains things, and it teaches you the same way."

Aur ye sirf Karpathy ke liye nahi — "once you've done this with Karpathy, you can do it with
pretty much anyone" (sales coach, author, jo bhi expert aap follow karte ho).

---

## 2. Timestamps (chapters)

| Time | Chapter | Kya hota hai |
|---|---|---|
| 0:00 | Karpathy's brain | Hook |
| 0:18 | Who is he? | Bio |
| 1:07 | Why bother? | Problem statement |
| 2:47 | 700K words | **Prompt 1** — crawl |
| 3:50 | His own wiki | **Prompt 2** — LLM Wiki gist paste |
| 5:37 | 7 rules | **Prompt 3** — rules extract (+ **Prompt 4** agent/skill) |
| 6:42 | Mini Karpathy | subagent + `/karpathy-teach` skill |
| 7:38 | Run it first | **Prompt 5** — hook / run gate |
| 8:48 | Would it ship? | **Prompt 6** — review test + `/karpathy-ingest` |

---

## 3. "Why bother" — do asli reasons

1. **Claude sirf code likhna chahta hai, samjhana nahi.** Video ke mutabik Karpathy ne khud
   publicly post kiya tha ki usne Claude Code se code ke saath-saath padhane ko kaha aur
   > "it didn't work at all because it really just wants to write code a lot more than it wants
   > to explain anything along the way."
2. **"The quality of what you build with AI comes down to the expertise that's in the system."**
   Aap har cheez ke expert nahi ban sakte — par expert ki poori soch system me daal sakte ho.

Closing line jo video chhodta hai:
> "You can outsource your thinking, but you cannot outsource your understanding."

---

## 4. 4 steps (video ka skeleton) — 6 prompts me

| Step | Kya | Output |
|---|---|---|
| 1 | Crawl — har source ke liye ek parallel agent | `raw/` me 1 subfolder per source, 700k+ words, ~45-60 min |
| 2 | Compile — Karpathy ke LLM Wiki gist ko paste karke wiki banao | `wiki/` with index + log + interlinked pages |
| 3 | Rules — har rule ke saath exact quote + source | 7 rules |
| 4 | Package + verify — subagent + skill + run hook, phir real test | mini-Karpathy jo run karke bolta hai |

**Crawl ke tools (video me):** YouTube ke liye `youtube-transcript-api` + `yt-dlp` (dono free),
X/Twitter ke liye **twitterapi.io** (paid, "2023 se ab tak ke saare posts ~$1 me").
Blogs/GitHub public hain. Crawl ki key trick: **ek agent per source, sab parallel**, aur
"write down what it got, so that you can actually check it" (= manifest).

---

## 5. Karpathy ka wo link aur idea — LLM Wiki gist

**Gist:** https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
(`llm-wiki.md`, created **4 April 2026**, 5000+ stars/forks)

Video me yahi gist "paste into the coding agent" wala step hai — aur ye funny part hai:
> "We're storing Karpathy's brain inside of Karpathy's own LLM wiki memory system."

Gist ka core (uske apne shabdon me, summarised):

- **RAG vs Wiki:** RAG har query par knowledge dobara se discover karta hai, kuch accumulate
  nahi hota. Iske bajaye LLM ko bolo ki wo sources ko ek **persistent, interlinked markdown wiki**
  me *compile* kare. "The wiki is a persistent, compounding artifact."
- **3 layers:**
  1. **Raw sources** — immutable. "The LLM reads from them but never modifies them."
  2. **The wiki** — "You read it; the LLM writes it." Summaries, entity pages, concept pages,
     comparisons, overview, synthesis.
  3. **The schema** — `CLAUDE.md` / `AGENTS.md`: conventions + workflows. "This is the key
     configuration file — it's what makes the LLM a disciplined wiki maintainer rather than a
     generic chatbot."
- **3 operations:** **Ingest** (ek source 10-15 pages touch karta hai), **Query** (index.md
  pehle padho, phir pages; aur acche answers wapas wiki me file karo), **Lint** (contradictions,
  stale claims, orphan pages, missing cross-refs dhundo).
- **index.md** = content catalog (har ingest pe update), **log.md** = append-only timeline with
  a parseable prefix: `## [2026-04-02] ingest | Article Title` →
  `grep "^## \[" log.md | tail -5`.
- **Tools:** Obsidian Web Clipper, attachments ko local download karna, **Obsidian graph view**
  ("the best way to see the shape of your wiki — what's connected to what, which pages are hubs,
  which are orphans"), Marp slides, Dataview, aur `qmd` (local hybrid BM25/vector search) jab
  wiki badi ho jaye. "The wiki is just a git repo of markdown files."
- **Kyun chalta hai:** "The tedious part of maintaining a knowledge base is not the reading or
  the thinking — it's the bookkeeping." LLM bore nahi hota, 15 files ek pass me update kar deta hai.
- Gist jaan-boojh ke abstract hai: "share it with your LLM agent and work together to instantiate
  a version that fits your needs."

Doosra Karpathy reference video me (July wala post): wo model se **10 minute voice me ramble**
karta hai aur phir model us text ko clean karta hai — isse `/karpathy-ingest` ka demo banta hai.

---

## 6. The 7 rules (video me jo nikle)

Har rule ke peeche ek **exact quote + source** hona chahiye; agar quote nahi hai to agent ko
bolna padta hai ki wo *infer* kar raha hai.

| # | Rule | Matlab (agent behaviour) |
|---|---|---|
| 1 | **Build it or you don't understand it** | explanation ke saath chalne wala artifact |
| 2 | **First-order term first** | jo ek piece matter karta hai use working dikhao, phir ek-ek cheez add karo |
| 3 | **Predict, then run, then compare** | cell chalane se pehle expected number bolo — warna "most of the time it will train, but silently work a bit worse" |
| 4 | **Show the wrong version first** | "he leaves his own bugs in the recording on purpose" |
| 5 | **Prove it, don't claim it** | bina run kiye "this works" nahi |
| 6 | **Say what you assumed** | uski #1 complaint: models wrong assumptions le lete hain aur bina check kiye chal padte hain |
| 7 | **Simpler wins** | jo cheez apni jagah earn nahi kar rahi, delete |

Video me ek aur detail: ek rule jiska sirf **ek** source tha wo "bench par" tha — naya ingest aane
par **doosra source mila aur wo real rule ban gaya**. Isliye is repo me har rule page par
`confidence: high | medium | inferred` field hai.

---

## 7. Mini-Karpathy ki packaging (video ka step 4)

- **Subagent** = alag Claude, apni instructions + apna context window ("so it doesn't drag your
  whole conversation along with it"). Usme 7 rules + bolne ka tareeka + har task ka loop.
- **Skill** = `/karpathy-teach <jis cheez par atke ho>` → task subagent ko jata hai, aur phir
  answer ko **checklist ke against grade** kiya jata hai, **one line per rule**.
- **Hook (run gate)** = ek chhota script jo agent ke turn khatam karte waqt chalta hai: agar code
  likha par chalaya nahi, to answer **block** ho jata hai aur wapas bhej diya jata hai —
  "Hey, you have to run this before you say it works."

Antigravity me hook nahi hai → is repo me wahi kaam `scripts/verify_gate.py` +
`.agents/rules/02-verification-gate.md` karte hain. Detail: `docs/ANTIGRAVITY-SETUP.md` §4.

---

## 8. Jo test video me chalaye gaye

- **BPE tokenizer banao aur samjhao** → agent ne pehle "done" define kiya, smallest version
  banaya, run se pehle prediction boli, real output dikhaya, phir **jaan-boojh ke broken version**
  dikhaya aur fix kiya, aur end me: kya run kiya | kya nikla | kya badla | kaunsa rule.
- **"Would the client accept this, and what would he want to delete?"** → ek YouTube-comments
  script jo Claude ke test me chal gayi thi; agent ne **predict** kiya ki normal Windows terminal
  par **emoji** par crash hogi, waise hi chala ke crash karwaya (aur wo **files likhne se pehle**
  crash hui) — matlab "it works" sirf ek specific terminal me sach tha. Phir delete-pass, aur
  trimmed version ko original ke saath side-by-side chala ke prove kiya.
- **`/karpathy-ingest <link>`** → ek post se rule 6 me naya behaviour add hua ("request patla ho
  to 2-3 sawaal pucho, guess mat karo"), ek bench-wala rule promote hua, aur index/log/hub pages
  khud update hue.

---

## 9. Fact-check (jo video kehta hai vs public record)

| Video claim | Status |
|---|---|
| OpenAI founding member (2015), Tesla AI ~5 saal, phir Eureka Labs | ✅ |
| "As of May this year he's at Anthropic on the pre-training team" | ✅ 19 May 2026 ko announce — Nick Joseph ke under, Claude se pre-training research accelerate karne wali nayi team |
| "One of Anthropic's **lead engineers**" | ⚠️ loose phrasing — wo pre-training researcher/team lead hai, title waisa nahi |
| Karpathy ne April me LLM Wiki gist post kiya | ✅ 4 April 2026 |
| X ka poora archive ~$1 me (twitterapi.io) | plausible, par rate card khud check kar lena |

---

## 10. Video me jo **nahi** bataya (par aapko chahiye hoga)

- Prompts ka verbatim text (sirf screen par dikhe) → maine reconstruct karke `PROMPTS.md` me
  Antigravity ke hisaab se likh diya hai.
- Crawl scripts ka code → `scripts/` me likh diya aur chala ke test kar liya.
- Legal side: ye sab **personal/research use** ke liye hai. Kisi ka naam/awaaz use karke public
  product mat banao, aur agent ko kabhi first-person "main Karpathy hoon" mat bolne do —
  isi liye persona file me likha hai: *"You never speak as him in first person."*
