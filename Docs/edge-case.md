# Edge Cases & Corner Scenarios

> AI-Powered Restaurant Recommendation System (Zomato Use Case)

**Sources:** [`Docs/context.md`](./context.md) · [`Docs/architecture.md`](./architecture.md) · [`Docs/implementation-plan.md`](./implementation-plan.md)

This document catalogs corner scenarios across every layer of the system. Each entry includes the scenario, expected system behavior, and recommended handling.

**Severity legend:**

| Level | Meaning |
|-------|---------|
| 🔴 Critical | Breaks core flow or risks bad recommendations |
| 🟠 High | Degrades UX or trust; must handle before demo |
| 🟡 Medium | Should handle gracefully; fallback acceptable |
| 🟢 Low | Rare or cosmetic; nice-to-have handling |

---

## Quick Reference Matrix

| Category | Count | Critical |
|----------|-------|----------|
| Data Layer | 18 | 4 |
| User Input | 16 | 2 |
| Filter Engine | 14 | 3 |
| Groq / LLM | 20 | 5 |
| Orchestration | 8 | 2 |
| UI / Presentation | 12 | 1 |
| Config & Environment | 10 | 2 |
| Deployment & Runtime | 9 | 2 |
| Security | 6 | 3 |

---

## 1. Data Layer

### 1.1 Dataset Loading

| ID | Scenario | Severity | Expected Behavior | Handling |
|----|----------|----------|-------------------|----------|
| D-01 | Hugging Face API unreachable (network down) | 🔴 | App cannot start without data | Retry once; load from local Parquet cache if available; show clear error with retry instructions |
| D-02 | Hugging Face dataset renamed or removed | 🔴 | Load fails permanently | Fail with message pointing to dataset URL; document manual CSV fallback in README |
| D-03 | Hugging Face rate limit / timeout | 🟠 | Slow or failed first load | Exponential backoff (max 2 retries); use cache on subsequent runs |
| D-04 | Dataset schema changed (column names differ) | 🔴 | Preprocessor breaks | Validate schema on load; fail fast with list of missing required columns |
| D-05 | Empty dataset returned (0 rows) | 🔴 | No restaurants to recommend | Abort startup; log error; UI shows "Dataset unavailable" |
| D-06 | Partial dataset download (corrupted) | 🟠 | Incomplete or malformed records | Validate row count against expected range; re-download if below threshold |
| D-07 | First startup — no cache exists | 🟡 | Long cold start (30s+) | Show loading indicator; persist to Parquet after successful load |
| D-08 | Cache file corrupted or unreadable | 🟡 | Cache load fails | Delete corrupt cache; re-fetch from Hugging Face |
| D-09 | Cache stale (dataset updated on HF) | 🟢 | Old data served | Optional cache TTL config; manual cache invalidation via env flag |

### 1.2 Data Preprocessing

| ID | Scenario | Severity | Expected Behavior | Handling |
|----|----------|----------|-------------------|----------|
| D-10 | Missing `name` field | 🟠 | Record unusable | Drop row; increment dropped-row counter in logs |
| D-11 | Missing `location` field | 🟠 | Cannot filter by city | Drop row or assign `"Unknown"` and exclude from location filter |
| D-12 | Missing `rating` field | 🟡 | Rating filter unreliable | Default to `0.0`; include in results but rank lower |
| D-13 | Invalid rating (e.g. `"-"`, `"NEW"`, `"4.5/5"`) | 🟡 | Type coercion fails | Parse numeric portion; default to `0.0` if unparseable |
| D-14 | Rating out of range (e.g. 6.0, -1.0) | 🟡 | Invalid comparisons | Clamp to `[0.0, 5.0]` |
| D-15 | Missing `cost` field | 🟡 | Budget filter skipped for row | Exclude from budget filter; still eligible via other filters |
| D-16 | Cost as string (e.g. `"₹500"`, `"500 for two"`, `"Moderate"`) | 🟠 | Budget tier mapping fails | Strip currency symbols; extract first numeric value; map qualitative labels to tiers |
| D-17 | Cost is zero or negative | 🟢 | Incorrect budget tier | Treat as `"unknown"`; exclude from budget filter |
| D-18 | Empty or null `cuisine` field | 🟡 | Cuisine filter misses/excludes row | Treat as `"Multi-cuisine"` or `"Unknown"`; exclude from strict cuisine match |
| D-19 | Multi-cuisine string (e.g. `"North Indian, Chinese, Mughlai"`) | 🟡 | Substring match may over/under-match | Normalize to lowercase; match if user cuisine appears as substring or token |
| D-20 | Duplicate restaurant names in same location | 🟡 | Ambiguous recommendations | Assign unique `id` per row (index/hash); disambiguate in UI if needed |
| D-21 | Special characters in name/location (unicode, emoji) | 🟢 | Display or match issues | Preserve unicode; normalize whitespace; case-fold for matching |
| D-22 | Very long restaurant name or cuisine string | 🟢 | UI overflow / token bloat | Truncate in LLM prompt at 200 chars; full name in UI |

---

## 2. User Input & Preference Parser

### 2.1 Required Fields

| ID | Scenario | Severity | Expected Behavior | Handling |
|----|----------|----------|-------------------|----------|
| U-01 | Location not provided (empty) | 🔴 | Cannot filter | Block submission; show validation error: "Location is required" |
| U-02 | Budget not selected | 🔴 | Cannot filter by cost | Block submission; show validation error: "Budget is required" |
| U-03 | Location not in dataset (e.g. `"Mumbai"` when absent) | 🟠 | Zero results | Fuzzy match against known cities; suggest closest: "Did you mean Bangalore?" |
| U-04 | Location with alternate spelling (e.g. `"Bengaluru"` vs `"Bangalore"`) | 🟠 | Zero results | Maintain alias map: `{ "bengaluru": "bangalore", "delhi": "new delhi" }` |
| U-05 | Location entered with extra whitespace/casing (`"  bangalore  "`) | 🟡 | May fail match | Trim and case-normalize before lookup |

### 2.2 Optional Fields

| ID | Scenario | Severity | Expected Behavior | Handling |
|----|----------|----------|-------------------|----------|
| U-06 | Cuisine left blank | 🟢 | No cuisine filter applied | Treat as `None`; skip cuisine filter step |
| U-07 | Cuisine not in dataset (e.g. `"Mexican"` in city with none) | 🟠 | Zero results after strict filter | Relax cuisine filter; inform user: "No Mexican found; showing similar options" |
| U-08 | Cuisine partial match (e.g. `"Indian"` matches `"North Indian"`) | 🟡 | Over-broad results | Substring match is acceptable; LLM refines ranking |
| U-09 | Min rating = 0.0 (default) | 🟢 | All ratings included | No rating filter applied |
| U-10 | Min rating = 5.0 (very strict) | 🟡 | Very few or zero results | Apply filter; trigger relaxation if zero matches |
| U-11 | Min rating out of slider range (API/CLI bypass) | 🟡 | Invalid input | Clamp to `[0.0, 5.0]` |
| U-12 | Additional preferences empty | 🟢 | LLM ranks on structured prefs only | Pass empty list; prompt omits additional section |
| U-13 | Additional preferences very long (500+ chars) | 🟡 | Token bloat / prompt overflow | Truncate to 300 chars; warn in UI |
| U-14 | Additional preferences with prompt injection attempt | 🔴 | LLM manipulation | Sanitize: strip system-like phrases; treat as plain user preference text only |
| U-15 | `top_k` requested > available candidates | 🟡 | Fewer results than requested | Return all available candidates; note count in metadata |
| U-16 | `top_k` = 0 or negative (API/CLI bypass) | 🟡 | Invalid request | Default to `DEFAULT_TOP_K` (5) |

---

## 3. Filter Engine

### 3.1 Zero & Low Match Scenarios

| ID | Scenario | Severity | Expected Behavior | Handling |
|----|----------|----------|-------------------|----------|
| F-01 | Zero matches after all strict filters | 🟠 | Empty result set | Progressive relaxation: cuisine → budget → min_rating (in order) |
| F-02 | Zero matches even after full relaxation | 🟠 | Still empty | Return empty list + suggest available locations/cuisines from dataset metadata |
| F-03 | Only 1 candidate matches | 🟡 | LLM receives single option | Pass single candidate; LLM returns 1 recommendation; UI shows 1 card |
| F-04 | Exactly N candidates (N = MAX_CANDIDATES_FOR_LLM) | 🟢 | Full context window used | Pass all; no truncation needed |
| F-05 | More than N candidates match (e.g. 200 in Bangalore) | 🟡 | Context window limit | Pre-rank by rating desc; take top N (default 20) before LLM |
| F-06 | All candidates have identical rating | 🟡 | Non-deterministic pre-rank | Secondary sort by name or id for stable ordering |

### 3.2 Filter Interaction Edge Cases

| ID | Scenario | Severity | Expected Behavior | Handling |
|----|----------|----------|-------------------|----------|
| F-07 | Budget "low" but all restaurants in city are "high" cost | 🟠 | Zero budget matches | Relax budget filter; notify user in metadata |
| F-08 | User selects "high" budget but wants cheap eats in additional prefs | 🟡 | Conflicting signals | Structured filter wins; LLM resolves conflict in explanation |
| F-09 | Min rating 4.5 filters out 95% of city restaurants | 🟡 | Very small candidate pool | Proceed with available candidates; LLM explains limited options |
| F-10 | Location has restaurants but none with parseable cost | 🟡 | Budget filter excludes all | Skip budget filter for that query; flag in metadata |
| F-11 | Cuisine filter on multi-cuisine restaurant | 🟢 | Should match if any token matches | Token/substring match across comma-separated cuisines |
| F-12 | Case mismatch in cuisine (`"italian"` vs `"Italian"`) | 🟢 | Should still match | Case-insensitive comparison |

### 3.3 Filter Relaxation Transparency

| ID | Scenario | Severity | Expected Behavior | Handling |
|----|----------|----------|-------------------|----------|
| F-13 | Filters relaxed without user knowing | 🟠 | User trust issue | Include `filters_relaxed: ["cuisine"]` in response metadata; surface in UI |
| F-14 | Multiple filters relaxed simultaneously | 🟡 | Over-broad results | Relax one at a time; stop at first non-zero result set |

---

## 4. Groq / LLM Layer

### 4.1 API & Connectivity

| ID | Scenario | Severity | Expected Behavior | Handling |
|----|----------|----------|-------------------|----------|
| L-01 | `GROQ_API_KEY` missing or empty | 🔴 | Cannot call LLM | Fail fast before API call; UI: "Configure GROQ_API_KEY in .env" |
| L-02 | Invalid / expired API key (401) | 🔴 | Auth failure | No retry; show setup instructions; fallback to filter-ranked results |
| L-03 | Groq rate limit (429) | 🟠 | Temporary failure | Exponential backoff, max 2 retries; then fallback to filter ranking |
| L-04 | Groq server error (500/503) | 🟠 | Transient failure | Retry once after 2s; fallback to filter ranking |
| L-05 | Request timeout (network slow) | 🟠 | Hung request | Set 30s timeout; fallback to filter ranking |
| L-06 | Model unavailable (`llama-3.3-70b-versatile` deprecated) | 🟠 | Model 404 | Fallback to secondary model (`llama-3.1-8b-instant`) if configured |
| L-07 | Groq account quota exhausted | 🔴 | All requests fail | Fallback to filter ranking; UI warning about LLM unavailability |

### 4.2 Response Parsing

| ID | Scenario | Severity | Expected Behavior | Handling |
|----|----------|----------|-------------------|----------|
| L-08 | LLM returns valid JSON | 🟢 | Normal path | Parse and validate directly |
| L-09 | LLM wraps JSON in markdown fences (` ```json ... ``` `) | 🟡 | Parse fails on raw text | Strip fences before JSON parse |
| L-10 | LLM returns malformed JSON (truncated, trailing comma) | 🟠 | Parse error | Retry once with repair prompt: "Return valid JSON only"; then fallback |
| L-11 | LLM returns empty response | 🟠 | No recommendations | Fallback to filter-ranked results |
| L-12 | LLM returns plain text instead of JSON | 🟠 | Parse error | Attempt regex JSON extraction; retry once; fallback |
| L-13 | LLM returns JSON missing required fields | 🟡 | Partial data | Fill missing fields from candidate records; drop entries without `restaurant_id` |
| L-14 | LLM returns extra fields not in schema | 🟢 | No impact | Ignore unknown fields |

### 4.3 Hallucination & Grounding

| ID | Scenario | Severity | Expected Behavior | Handling |
|----|----------|----------|-------------------|----------|
| L-15 | LLM recommends restaurant not in candidate list | 🔴 | Ungrounded recommendation | `RecommendationValidator` rejects; drop hallucinated entries |
| L-16 | LLM invents `restaurant_id` | 🔴 | Merge fails | Reject entry; log warning |
| L-17 | LLM duplicates same restaurant at multiple ranks | 🟡 | Redundant results | Deduplicate by `restaurant_id`; keep highest rank |
| L-18 | LLM returns fewer than `top_k` recommendations | 🟡 | Partial result | Backfill remaining slots from filter-ranked candidates not yet included |
| L-19 | LLM returns more than `top_k` recommendations | 🟡 | Too many results | Truncate to `top_k` by rank |
| L-20 | LLM assigns non-sequential ranks (1, 3, 5) | 🟢 | Display inconsistency | Re-normalize ranks to 1..N after validation |
| L-21 | LLM explanation contradicts user preferences | 🟡 | Trust issue | Accept (explanation quality varies); log for prompt tuning |
| L-22 | LLM explanation is generic ("Great restaurant!") | 🟡 | Low value | Prompt requires referencing specific prefs; acceptable for v1 |
| L-23 | LLM summary absent when optional | 🟢 | Missing overview | Set `summary: null`; UI hides summary block |

### 4.4 Prompt & Token Edge Cases

| ID | Scenario | Severity | Expected Behavior | Handling |
|----|----------|----------|-------------------|----------|
| L-24 | Candidate list exceeds context window | 🟠 | API error or truncation | Cap at `MAX_CANDIDATES_FOR_LLM` (20); include only essential fields |
| L-25 | Additional preferences contain adversarial prompt text | 🔴 | Prompt injection | Wrap in delimiters; instruct LLM to treat as user preference data only |
| L-26 | All candidates have identical attributes | 🟡 | LLM cannot differentiate | LLM still ranks/explains based on name and additional prefs; acceptable |

---

## 5. Orchestration (RecommendationService)

| ID | Scenario | Severity | Expected Behavior | Handling |
|----|----------|----------|-------------------|----------|
| O-01 | Full happy path | 🟢 | Ranked results with explanations | Return `RecommendationResponse` with `llm_used: true` |
| O-02 | Filter succeeds, LLM fails | 🟠 | Partial experience | Return filter-ranked results with `llm_used: false`; generic or no explanation |
| O-03 | Filter returns empty, LLM never called | 🟠 | No recommendations | Return empty list + suggestions; do not call LLM |
| O-04 | LLM succeeds but all recommendations hallucinated | 🔴 | Empty after validation | Fallback to filter-ranked results entirely |
| O-05 | Concurrent requests (multiple UI clicks) | 🟡 | Duplicate Groq calls | Disable submit button during processing; optional request deduplication |
| O-06 | RestaurantStore not initialized (startup race) | 🔴 | AttributeError | Ensure store loads in `@st.cache_resource` or app startup before serving |
| O-07 | Partial LLM validation (3 of 5 valid) | 🟡 | Reduced result set | Return 3 valid; backfill 2 from filter ranking if below `top_k` |
| O-08 | Exception in any pipeline stage | 🟠 | Unhandled crash | Catch at service boundary; return error response with safe message (no stack trace to UI) |

---

## 6. UI / Presentation Layer

| ID | Scenario | Severity | Expected Behavior | Handling |
|----|----------|----------|-------------------|----------|
| P-01 | User clicks "Get Recommendations" repeatedly | 🟡 | Duplicate API calls | Disable button + show spinner until response received |
| P-02 | Groq call takes > 5s | 🟡 | User uncertainty | Show loading spinner with "Finding restaurants..." message |
| P-03 | Zero results returned | 🟠 | Blank screen confusion | Show empty state: "No restaurants found" + suggestions |
| P-04 | Results contain null cost | 🟡 | Display `"None"` or blank | Show "Cost not available" |
| P-05 | Results contain rating 0.0 | 🟡 | Looks like bad restaurant | Display "Unrated" or "New" instead of 0.0 stars |
| P-06 | Very long LLM explanation | 🟢 | UI layout break | Render in expandable card; truncate preview to 3 lines |
| P-07 | Missing `GROQ_API_KEY` on startup | 🔴 | Silent failure on submit | Check key on load; show banner with setup instructions |
| P-08 | Streamlit session reload mid-request | 🟡 | Stale or lost state | `@st.cache_resource` for store; form state resets acceptably |
| P-09 | Location dropdown with 100+ cities | 🟢 | Hard to navigate | Sort alphabetically; optional search/filter in selectbox |
| P-10 | Mobile/narrow viewport | 🟢 | Layout issues | Use Streamlit columns responsively; stack cards vertically |
| P-11 | Filters relaxed — user not informed | 🟠 | Confusing results | Show info banner: "Expanded search: cuisine filter relaxed" |
| P-12 | LLM fallback used — no explanations shown | 🟡 | Reduced value | Show note: "AI explanations unavailable; showing top-rated matches" |

---

## 7. Configuration & Environment

| ID | Scenario | Severity | Expected Behavior | Handling |
|----|----------|----------|-------------------|----------|
| C-01 | `.env` file missing | 🟠 | Defaults used; no API key | Use defaults; Groq calls fail gracefully with clear message |
| C-02 | Invalid `LLM_MODEL` name | 🟠 | Groq 404 | Log error; try fallback model; then filter-only mode |
| C-03 | `MAX_CANDIDATES_FOR_LLM` set to 0 or negative | 🟡 | Empty prompt candidates | Enforce minimum of 1; default to 20 |
| C-04 | `MAX_CANDIDATES_FOR_LLM` set very high (e.g. 500) | 🟡 | Context overflow | Cap at 50 regardless of env value |
| C-05 | Budget thresholds misconfigured (LOW > MEDIUM) | 🟡 | Incorrect tier mapping | Validate thresholds on startup; fail fast if LOW ≥ MEDIUM |
| C-06 | `DEFAULT_TOP_K` > `MAX_CANDIDATES_FOR_LLM` | 🟡 | Cannot fill top_k | Cap top_k at candidate count |
| C-07 | `LLM_TEMPERATURE` out of range | 🟢 | Unpredictable output | Clamp to `[0.0, 1.0]` |
| C-08 | Multiple `.env` files (.env vs .env.local) | 🟢 | Wrong config loaded | Document precedence: `.env.local` > `.env` > defaults |
| C-09 | Environment variable type mismatch (string `"5"` for top_k) | 🟡 | Type error | Coerce to int with fallback to default |
| C-10 | Missing write permission for cache directory | 🟡 | Cache save fails | Log warning; run in-memory only without cache |

---

## 8. Deployment & Runtime

| ID | Scenario | Severity | Expected Behavior | Handling |
|----|----------|----------|-------------------|----------|
| R-01 | Cloud cold start — HF download on first request | 🟠 | Timeout on Streamlit Cloud | Pre-build Parquet cache; commit to repo or build step; or bundle data |
| R-02 | Streamlit Cloud memory limit exceeded | 🟠 | App crash | Use Parquet cache; load only required columns; avoid duplicate DataFrames |
| R-03 | Secret not configured in deployment platform | 🔴 | All LLM calls fail | Document required secrets; health check on startup |
| R-04 | Groq IP blocked in deployment region | 🟠 | API unreachable | Fallback to filter-only mode; document region requirements |
| R-05 | App idle timeout during long Groq call | 🟡 | Request dropped | Keep Groq timeout < platform request timeout (30s) |
| R-06 | Multiple simultaneous users on demo URL | 🟡 | Rate limit hit faster | Acceptable for fellowship demo; add note in README |
| R-07 | Python version mismatch (3.9 vs 3.10+) | 🟡 | Syntax/runtime errors | Pin `python_version` in deployment config |
| R-08 | Dependency version conflict on deploy | 🟡 | Install failure | Pin versions in `requirements.txt` |
| R-09 | Disk full — cache write fails | 🟢 | Non-fatal | Log warning; continue without cache |

---

## 9. Security

| ID | Scenario | Severity | Expected Behavior | Handling |
|----|----------|----------|-------------------|----------|
| S-01 | API key committed to git | 🔴 | Credential leak | `.gitignore` `.env`; use `.env.example` with placeholders only |
| S-02 | API key logged in debug output | 🔴 | Credential leak | Never log `GROQ_API_KEY` or full prompt headers |
| S-03 | Prompt injection via additional preferences | 🔴 | LLM behavior manipulation | Sanitize input; delimiter wrapping; system prompt guardrails |
| S-04 | User input logged verbatim in production | 🟡 | Privacy concern | Log preference categories, not raw free-text (optional) |
| S-05 | SSRF via dataset URL manipulation | 🟢 | Not applicable if URL hardcoded | Hardcode HF dataset ID; do not accept user-supplied URLs |
| S-06 | Excessive API calls (accidental loop) | 🟡 | Cost / rate limit | Rate limit at UI (disable button); max 1 concurrent Groq call per session |

---

## 10. Cross-Cutting Scenarios

### 10.1 End-to-End User Journeys

| ID | Journey | Key Edge Cases | Expected Outcome |
|----|---------|----------------|------------------|
| X-01 | First-time user, valid prefs, LLM works | — | 5 ranked cards with explanations + summary |
| X-02 | Pickiest user (5.0 rating, high budget, rare cuisine) | F-01, F-09, L-18 | Relaxed filters or fewer results with transparent messaging |
| X-03 | Minimal user (location + budget only) | U-06, U-09 | Broad results; LLM explains based on available signals |
| X-04 | Demo without internet (after first load) | D-01, L-01 | Cached data works; LLM fails → filter-only results |
| X-05 | Demo with no API key | L-01, P-07 | Filter-ranked results or clear setup banner |
| X-06 | City with 3 restaurants total | F-03, U-15 | Return 3 results max; no padding with hallucinations |

### 10.2 Data + Filter + LLM Interaction

| ID | Scenario | Severity | Expected Behavior |
|----|----------|----------|-------------------|
| X-07 | Restaurant passes filter but has no rating and no cost | 🟡 | Included in candidates; LLM explanation notes limited info |
| X-08 | User additional pref "vegetarian" but dataset has no dietary field | 🟡 | Passed to LLM only; LLM infers from cuisine/name if possible; no guarantee |
| X-09 | Same user submits identical query twice | 🟢 | Same results (deterministic filter + low temp LLM); acceptable |
| X-10 | Budget tier thresholds don't match dataset cost scale | 🟠 | All restaurants in one tier | Recalibrate thresholds after Phase 1 dataset exploration |

---

## 11. Fallback Decision Tree

```
User submits preferences
        │
        ▼
  Valid input? ──No──▶ Return validation error (U-01, U-02)
        │ Yes
        ▼
  Apply strict filters
        │
        ▼
  Any matches? ──No──▶ Relax filters (F-01) ──Still none?──▶ Empty + suggestions (F-02)
        │ Yes
        ▼
  Cap at N candidates (F-05)
        │
        ▼
  GROQ_API_KEY set? ──No──▶ Filter-ranked fallback (L-01)
        │ Yes
        ▼
  Call Groq API
        │
        ├─ Success ──▶ Parse JSON (L-08–L-12)
        │                   │
        │                   ├─ Valid ──▶ Validate IDs (L-15–L-17)
        │                   │               │
        │                   │               ├─ Enough results ──▶ Return with llm_used: true
        │                   │               └─ Too few ──▶ Backfill from filter (L-18, O-07)
        │                   │
        │                   └─ Invalid ──▶ Retry once (L-10) ──Fail──▶ Filter fallback
        │
        └─ Failure (L-03–L-07) ──▶ Filter-ranked fallback (llm_used: false)
```

---

## 12. Test Case Checklist

Use this checklist during Phase 6 testing. Mark each scenario as ✅ handled or ❌ open.

### Data Layer
- [ ] D-01: HF unreachable, cache exists
- [ ] D-01: HF unreachable, no cache
- [ ] D-10: Row with missing name dropped
- [ ] D-16: Cost string `"₹1,200 for two people"` parsed correctly
- [ ] D-18: Empty cuisine treated as Unknown/Multi-cuisine

### User Input
- [ ] U-01: Empty location blocked
- [ ] U-03: Unknown city shows suggestion
- [ ] U-04: Bengaluru → Bangalore alias works
- [ ] U-14: Prompt injection in additional prefs neutralized

### Filter Engine
- [ ] F-01: Zero matches triggers relaxation
- [ ] F-05: 200 matches capped at N=20
- [ ] F-13: Relaxed filters reported in metadata

### Groq / LLM
- [ ] L-01: Missing API key → clear error + fallback
- [ ] L-03: 429 rate limit → retry then fallback
- [ ] L-09: JSON in markdown fences parsed
- [ ] L-10: Malformed JSON → repair retry → fallback
- [ ] L-15: Hallucinated restaurant_id rejected
- [ ] L-18: Partial LLM response backfilled

### UI
- [ ] P-03: Zero results empty state
- [ ] P-07: Missing API key banner on load
- [ ] P-11: Filter relaxation info banner shown
- [ ] P-12: LLM fallback note displayed

### End-to-End
- [ ] X-01: Bangalore + medium + Italian + 4.0 rating
- [ ] X-02: Strict prefs → relaxation or few results
- [ ] X-04: Offline mode with cache
- [ ] X-05: No API key demo mode

---

## 13. Priority Implementation Order

Handle these edge cases first — they have the highest impact on demo reliability:

| Priority | IDs | Reason |
|----------|-----|--------|
| 1 | L-01, L-15, L-16, F-01, U-01 | Core correctness and grounding |
| 2 | L-03, L-10, O-02, D-01 | Graceful degradation paths |
| 3 | U-03, U-04, F-13, P-03, P-07 | User-facing clarity |
| 4 | D-16, D-18, F-05, L-09 | Data quality and parsing robustness |
| 5 | All remaining 🟢 Low items | Polish and edge polish |

---

## References

- [`Docs/context.md`](./context.md)
- [`Docs/architecture.md`](./architecture.md) — §12 Error Handling & Edge Cases
- [`Docs/implementation-plan.md`](./implementation-plan.md) — Phase 6 testing tasks
