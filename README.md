<h1 align="center">Swarnika Somvanshi</h1>

<p align="center">
  <b>Backend engineer in the making.</b> I build systems from the protocol up, then measure them and fix what breaks.<br/>
  <sub>Scaler School of Technology · BITS Pilani (CS, 2028) · Bengaluru</sub>
</p>

<p align="center">
  <a href="https://linkedin.com/in/swarnika-somvanshi"><img src="https://img.shields.io/badge/LinkedIn-0A66C2?style=flat-square&logo=linkedin&logoColor=white" alt="LinkedIn" /></a>
  <a href="https://my-portfolio-nine-gold-84.vercel.app"><img src="https://img.shields.io/badge/Portfolio-161b22?style=flat-square&logo=vercel&logoColor=white" alt="Portfolio" /></a>
  <a href="mailto:somvanshiswarnika@gmail.com"><img src="https://img.shields.io/badge/Email-EA4335?style=flat-square&logo=gmail&logoColor=white" alt="Email" /></a>
</p>

<p align="center">
  <a href="https://github.com/swarnika-cmd/HTTP-1.1-Server">
    <img src="assets/terminal.svg" width="760" alt="A real curl -i against my HTTP/1.1 server" />
  </a>
</p>

<p align="center"><sub>☝️ Not a mockup. Every Monday, CI compiles my <a href="https://github.com/swarnika-cmd/HTTP-1.1-Server">HTTP/1.1 server</a>, starts it, runs that <code>curl</code>, and re-renders this card from the real response.</sub></p>

## 📊 Numbers, not adjectives

<a href="#-what-i-built"><img src="assets/bench.svg" width="100%" alt="Benchmark results" /></a>

<sub>Rendered from the benchmark results committed in each repo (`bench/results/`). Apple M4 Pro, Docker, wrk and k6. Local numbers for comparing designs, not production capacity.</sub>

## 🧱 What I built

| | Project | The interesting part |
|:-:|---|---|
| ⚡ | **[HTTP/1.1 Server](https://github.com/swarnika-cmd/HTTP-1.1-Server)**<br/><sub>Java 21 · raw sockets · 47 tests</sub> | A bounded worker pool with 503 load shedding vs virtual threads: keep-alive connections pin platform threads, so virtual threads cut p99 by 12× |
| 🔎 | **[Search Typeahead](https://github.com/swarnika-cmd/SearchTypeahead)**<br/><sub>TypeScript · SQLite · 67 tests</sub> | Precomputed top-K at every trie node makes lookups O(prefix length); the cost is memory, measured at 4.4 GB for 1M terms |
| 🛡️ | **[ShieldWall Gateway](https://github.com/swarnika-cmd/ShieldWall-Gateway)**<br/><sub>FastAPI · Postgres · Redis · 88 tests</sub> | PII masked before it leaves, restored mid-stream across SSE chunks; budgets reserved atomically in a Redis Lua script |
| 🧠 | **[Smarana](https://github.com/swarnika-cmd/Smarana-PrivacyFirstBrain)**<br/><sub>Chrome MV3 · FastAPI · pgvector</sub> | On-device embeddings and AES-256-GCM, with hybrid search fused by Reciprocal Rank Fusion |

<details>
<summary><b>🔬 Architecture and the bugs I fixed (click to expand)</b></summary>
<br/>

**⚡ HTTP/1.1 Server**

```mermaid
flowchart LR
    C([client]) -->|TCP| A[accept loop]
    A --> Q{{bounded queue}}
    Q -- full --> X[503 + Retry-After]
    Q --> W[platform pool or<br/>virtual threads]
    W --> P[byte parser<br/>Content-Length / chunked]
    P --> H[handlers]
```
Fixed with a failing raw-socket test first: a lowercase `content-length` desynced the connection, a UTF-8 body swallowed the next request, a negative `Content-Length` dropped the socket, and slow clients could pin every worker.

**🔎 Search Typeahead**

```mermaid
flowchart LR
    K([keystroke]) --> R{consistent-hash ring}
    R --> S1[(cache shard)] & S2[(cache shard)] & S3[(cache shard)]
    S1 & S2 & S3 -- miss --> T[trie · top-10 per node]
    W([search]) --> B[write-behind buffer] -->|batched txn| D[(SQLite)]
```
Fixed 10 bugs, including buffered searches lost at the hour boundary, `c++` and `c--` colliding in one trie node, and a half-committed batch on a failed flush. A brute-force property test caught a trailing-space bug.

**🛡️ ShieldWall Gateway**

```mermaid
flowchart LR
    C([client]) --> K[API key · sha256] --> M[mask PII] --> B[Lua budget reserve] --> U[(provider)]
    U -->|SSE| S[unmask across chunks] --> C
    S -. reconcile .-> B
    S -. log .-> Q[[Celery]] --> P[(Postgres)]
```
Proved a check-then-act budget race with 50 concurrent requests (the budget fits 7; now exactly 7 succeed). Also fixed placeholder collisions that returned the wrong user's PII.
</details>

## 🌍 Merged

<a href="https://github.com/search?q=author%3Aswarnika-cmd+is%3Apr+is%3Amerged&type=pullrequests"><img src="assets/oss.svg" width="100%" alt="My merged pull requests" /></a>

<sub>Mentored by Naomi Carrigan in the freeCodeCamp × NHCarrigan Summer 2026 cohort.</sub>

## 🧰 Toolbox

<p>
  <img src="https://skillicons.dev/icons?i=java,python,ts,nodejs,express,fastapi,nextjs,supabase,postgres,redis,sqlite,docker,githubactions,git,bash&perline=15" alt="Java, Python, TypeScript, Node.js, Express, FastAPI, Next.js, Supabase, PostgreSQL, Redis, SQLite, Docker, GitHub Actions, Git, Bash" />
</p>

---

<sub>This page builds itself: <a href=".github/workflows/render-profile.yml"><code>render-profile.yml</code></a> compiles and curls my server, reads the benchmark files from my repos, and queries the GitHub API for merged PRs. Then <a href="scripts/render.py"><code>render.py</code></a> (standard-library Python) draws the cards. No third-party stat widgets, so nothing on this page can go down.</sub>
