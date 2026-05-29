# Target app: Phoenix docs Q&A bot

## Decision
The SRE agent monitors a small RAG/FAQ bot that answers questions about
**Arize Phoenix** — its concepts, APIs, MCP server, and tracing setup. This is
supporting infrastructure for the project, not the project itself.

## Why this domain
- **Recursive narrative.** "An agent that fixes a Q&A bot built on Phoenix,
  using Phoenix to do it." The story is self-evident; the demo writes itself.
- **Free, abundant ground truth.** Phoenix docs are publicly available, so
  expected answers can be sourced and verified without licensing concerns.
- **Realistic failure modes.** A docs bot can regress in all the ways a real
  production LLM app does — outdated info, hallucination, refusal loops,
  formatting violations — which gives the SRE agent realistic clustering work.
- **No safety overhang.** Unlike healthcare or finance, prompt regressions here
  have low real-world consequence, so we can introduce regressions
  deliberately for demo purposes without ethical concerns.
- **Judges already know the domain.** Arize judges (Richard Young, Clay Miner)
  will instantly recognize when the bot answers Phoenix questions wrong, which
  makes the demo's "before" state visceral.

## Out of scope
- The target app is **not** the submission. Effort spent on it should be
  hours, not days. It just needs to be a believable RAG bot with a prompt
  that can regress.
- We do not need a polished UI for the target app. A small FastAPI service
  with one `/ask` endpoint is enough.
- We do not need RAG over the full Phoenix docs corpus. A small curated set of
  doc chunks (20-40 chunks covering install, tracing, datasets, experiments,
  prompts, MCP) is sufficient.

## Tech outline (to be built in Build Phase 3)
- Small FastAPI app, deployed to its own Cloud Run service.
- Gemini 2.5 Flash for answering, with the system prompt stored in the Phoenix
  prompt registry under the name `phoenix-faq-bot.system`.
- RAG over ~30 markdown chunks scraped from `arize.com/docs/phoenix`,
  committed to the target-app repo as static content (no live scraping).
- Instrumented with `openinference-instrumentation-google-genai` so every
  call produces a Phoenix trace.
- LLM-as-judge eval continuously running against a small held-out set so
  Phoenix has real eval scores to alert on.

## Repository layout
The target app lives in a **separate public GitHub repo**:
`github.com/bekiTil/phoenix-faq-bot` (to be created in Build Phase 3).
The SRE agent opens PRs against that repo when it proposes prompt fixes.

## Failure modes the regression introducer will exercise
The eight failure modes from `evals/schema.py`:
- `outdated_info` (e.g. claim Phoenix is npm-installable)
- `hallucination` (e.g. invent a model name or API)
- `wrong_product` (e.g. confuse Phoenix with Arize AX)
- `refusal_loop` (e.g. bot refuses to give code examples)
- `formatting_violation` (e.g. break expected markdown structure)
- `safety_overreach` (e.g. add unnecessary safety preamble to every answer)
- `truncation` (e.g. answers cut off mid-sentence)
- `citation_missing` (e.g. confident claims with no doc link)

Each failure mode corresponds to a deliberately bad prompt variant the
regression introducer can install on demand to drive the SRE agent's demo.
