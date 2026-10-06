# Visual graph — wo "purple links" wala relationship map

Video me jo Obsidian ka graph/links dikh rahe the, wo alag se banaya hua feature nahi hai —
wo **wiki ke `[[links]]` ka side-effect** hai. Karpathy ne gist me bhi yahi likha:

> "Obsidian's graph view is the best way to see the shape of your wiki — what's connected to
> what, which pages are hubs, which are orphans."

Aapke paas do raaste hain. Dono ek hi `wiki/` folder par kaam karte hain.

---

## Option A — Obsidian (zero setup, sabse pretty)

1. Obsidian kholo → **Open folder as vault** → is repo ka `wiki/` folder choose karo.
2. Graph view (Ctrl/Cmd+G). Bas. `[[wiki-links]]` Obsidian-compatible likhe gaye hain.
3. Settings → Appearance → Graph me **colour groups** bana lo:
   `path:rules` red · `path:sources` grey · `path:topics` blue · `path:methods` green ·
   `path:principles` purple · `path:people` orange.
4. Karpathy ka workflow: **ek taraf Antigravity, doosri taraf Obsidian.**
   > "The LLM makes edits based on our conversation, and I browse the results in real time —
   > following links, checking the graph view... Obsidian is the IDE; the LLM is the programmer;
   > the wiki is the codebase."

Bonus plugins jo gist bolta hai: **Dataview** (frontmatter par queries — isiliye har page me
`type`, `confidence`, `last_updated` hai) aur **Marp** (wiki se slides).

---

## Option B — repo ka apna graph (Antigravity khud bana aur dikha sakta hai)

Obsidian ki dependency nahi chahiye, aur agent **khud** build karke screenshot le sakta hai:

```bash
python scripts/build_graph.py --wiki wiki --out wiki/_graph
python -m http.server 8080 --bind 0.0.0.0 --directory wiki/_graph
# open http://localhost:8080/graph.html
```

Ya seedha chat me: **`/wiki-graph`**

Teen output milte hain:

| File | Kya |
|---|---|
| `graph.html` | interactive force graph (vis-network), search box, click par "cited by / cites" |
| `graph.json` | nodes + edges + metrics — kisi aur tool me daal sakte ho |
| `graph.md` | Mermaid fallback (top 60 nodes) — GitHub/preview me seedha render hota hai |

Colour = page type, node size = **in-degree** (kitne pages isko cite karte hain),
arrow = citing → cited.

Useful flags:

```bash
--min-degree 1              # orphans chhupa do
--type rules,sources        # sirf rule→source coverage dekhni hai
--max-nodes 400             # badi wiki ko readable rakho
```

Terminal par ye summary bhi print hoti hai (fixture par actually test kiya gaya):

```
pages=7 links=13 types={'index': 1, 'method': 2, 'rule': 2, 'source': 1, 'topic': 1}
hubs: methods/how-he-debugs(3), rules/predict-then-run(3), topics/tokenization(3)
orphans: methods/orphan-page
weak rules: rules/predict-then-run, rules/simpler-wins
broken links: rules/predict-then-run->sources/missing-page
```

---

## Graph ko padhna kaise hai (ye asli value hai, dekhna nahi)

| Signal | Matlab | Action |
|---|---|---|
| **Hub** (sabse zyada inbound) | brain ka asli centre | ensure karo ki ye page sach me accha likha hai |
| **Orphan** (0 links) | ye knowledge kabhi retrieve nahi hogi | backlinks add karo ya delete |
| **Bridge** (do clusters ko jodta node) | sabse valuable page | isko expand karo |
| **Weak rule** (<2 distinct source links) | rule abhi "bench par" hai | aur sources ingest karo, warna `confidence: medium` |
| **Lopsided cluster** (30 sources, 0 method page) | capture hua, compression nahi | missing `methods/` page likhwao |
| **Broken link** | agent ne jo page maana wo hai hi nahi | `/wiki-lint` → fix |

Video wali line yahi graph prove karta hai: har rule apne **sources** se juda hona chahiye, aur
har source un **rules** ko point kare jinko wo support karta hai. Graph me agar koi `rules/` node
akela latak raha hai — wo rule abhi sach me "uska" rule nahi hai, aapka guess hai.

---

## Agent ko kya bolna hai

```
/wiki-graph
```

ya detail me:

```
Build the wiki graph, serve it on 8080, open it in the browser tool and screenshot it.
Then tell me: top 5 hubs, every orphan, every rule with fewer than 2 distinct source links,
and the 3 pages I should write next to connect the weakest cluster. Don't just give me a path —
show me the picture and read it back to me.
```

---

## Aur agar poora status page chahiye

Graph + health score + rule coverage + crawl stats + run-gate log, sab ek page par:
`/dashboard` ya `python scripts/dashboard.py --wiki wiki --raw raw` → `docs/DASHBOARD.md`.
