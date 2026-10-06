# example-wiki — DEMO ONLY

Ye asli wiki nahi hai. Ye sirf **structure ka demo** hai taaki aap `/wiki-graph` ka output
aaj hi dekh sako, aur page format samajh aa jaye. Isme koi real quote nahi hai — har page par
"DEMO PAGE" likha hua hai.

```bash
python scripts/build_graph.py --wiki docs/example-wiki --out docs/example-wiki/_graph
python -m http.server 8080 --bind 0.0.0.0 --directory docs/example-wiki/_graph
# http://localhost:8080/graph.html
```

28 pages · 78 links · 0 orphans · 2 "weak rules" (jinke peeche 2 se kam source hain) — exactly
wahi signals jo asli wiki par dekhne hain.

Asli kaam `wiki/` me hota hai. Jab `/build-wiki` chal jaye, is folder ko delete kar dena.
