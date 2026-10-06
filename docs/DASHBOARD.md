# Dashboard — brain ki health ek hi page par

Video me dashboard nahi tha (wahan sirf Obsidian ka graph tha). Par 700k words aur 100+ pages ke
baad aapko ye sawaal roz chahiye hote hain: *kitna capture hua? kaunsa rule abhi guess hai?
agent ne code chalaya bhi ya nahi?* — isliye `scripts/dashboard.py` bana diya.

**Abhi live chal raha hai** (demo data par) — preview me khul raha hoga.

```bash
# asli brain par
python scripts/dashboard.py --wiki wiki --raw raw --port 8081
# http://localhost:8081

# demo data (28 pages, koi real quote nahi)
python scripts/dashboard.py --wiki docs/example-wiki --port 8081

# sirf numbers, bina server ke (agent ke liye useful)
python scripts/dashboard.py --once
```

Chat me: **`/dashboard`** — agent khud build karega, server start karega, browser me kholega,
screenshot lega aur numbers **padh ke sunayega**.

---

## Kya dikhata hai

| Panel | Kya batata hai | Kyun matter karta hai |
|---|---|---|
| **Health score** | 7 checks: corpus captured · wiki compiled · broken links · orphans · rules quote-backed · rules on 2+ sources · runs logged | ek number me pata chal jata hai ki brain bharosemand hai ya abhi aadha |
| **Raw corpus** | per source type: files + words + bar | kaunsa source thin hai (jaise X skip ho gaya) |
| **Wiki** | pages, links, words, type-wise chips | capture vs compression ka balance |
| **Rule coverage** | har rule: kitne **distinct sources**, kitne quotes, confidence | 🟢 2+ sources = asli rule · 🟡 1 = bench par · 🔴 0 = sirf aapka guess |
| **Top hubs** | sabse zyada cite hone wale pages | brain ka asli centre |
| **Activity** | `wiki/log.md` ka sparkline + last 12 entries | kaam ruk to nahi gaya, kya-kya hua |
| **Run gate** | `.state/run_log.jsonl`: total / passed / failed + last 10 commands | proof ki "it works" bina chalaye nahi bola gaya |
| **Graph** | wahi interactive graph, embed kiya hua | shakal + orphans + clusters |

Har 20 second me khud refresh hota hai, aur har refresh par graph dobara build hota hai —
matlab `/karpathy-ingest` chalate hi numbers hil jayenge.

---

## Health checks ka matlab

| Check | Pass kab | Fail ho to karo |
|---|---|---|
| sources captured | `raw/` me 50k+ words | `/crawl-sources` |
| wiki compiled | 20+ pages | `/build-wiki` |
| no broken links | 0 broken | `/wiki-lint` |
| no orphans | 0 orphan pages | backlinks add karo ya delete |
| rules quote-backed | har rule par quote ya `confidence: inferred` | `/extract-rules` dobara |
| rules on 2+ sources | har rule ke 2 distinct source links | aur sources ingest karo |
| runs logged | kam se kam 1 logged run | code hamesha `scripts/run_and_log.py` se chalao |

Demo data par abhi **71%** aata hai (raw khali hai, aur 7 me se 5 rules strong hain) — ye
jaan-boojh ke honest hai, 100% dikhana aasaan hota par bekaar hota.

---

## Implementation notes

- **Pure stdlib** — koi dependency nahi (`http.server` + `json`). Port kahin bhi, host `0.0.0.0`
  taaki remote/preview me bhi khule.
- **Read-only** — sirf `wiki/_graph/` regenerate karta hai, aur kuch nahi chhuta.
- Endpoints: `/` (page), `/api/stats` (JSON — isko aap apne tools me bhi use kar sakte ho),
  `/graph/graph.html` (embedded graph).
- Dusre expert ke liye reuse: kuch badalne ki zarurat nahi, bas `--wiki` path do.
