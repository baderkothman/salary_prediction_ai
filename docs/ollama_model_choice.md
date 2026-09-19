# Ollama Model Choice

Two models were available locally: `qwen3:4b` and `llama3.2:latest`. Both were tested against the real running Ollama server (not assumed from documentation) with the exact prompt/schema used by `scripts/llm_client.py`.

## `qwen3:4b` — rejected

`qwen3:4b` is a reasoning ("thinking") model. With Ollama's default settings, its entire output goes into a separate `thinking` field and `response` is left empty — confirmed directly:

```json
"response": "",
"thinking": "{\n  \"ok\": true\n}",
```

Setting `"think": false` in the request routes output into `response` as expected, but the model then loses the ability to follow the task: given the analysis context as input, it just echoed the input JSON straight back as its "response," regardless of prompt wording (tested with the context embedded directly as the prompt, and again with an explicit instruction sentence prepended). This happened consistently across all 3 retry attempts.

## `llama3.2:latest` — selected

Not a reasoning model, so `response` is populated normally. Given the same context and system prompt, it produced a genuinely grounded analysis on the first or second attempt (occasional minor schema misses — e.g. `limitations` returned as a string instead of a list — are exactly what the bounded-retry loop in `generate_salary_analysis` exists to absorb):

- Correctly stated the prediction ($147,754.79) was above the peer median ($144,000).
- Referenced multiple supplied attributes (experience level, employment type, company location).
- Included a sample-size caveat ("n=49... interpreted with caution") without being asked for that specific number.
- Produced a valid `bar` chart spec with matching `x`/`y` lengths.

## Known limitation: schema-valid but logically wrong direction

In one run, `llama3.2:latest` correctly quoted both numbers from the supplied context ("$58,000" predicted vs. "$59,500" peer median) but stated the prediction was "above" the median -- $58,000 is below $59,500. This passes schema validation (it's well-formed JSON referencing real numbers, exactly what Pydantic checks) but is a genuine reasoning error from a small (3B) local model, not a pipeline bug. It was also seen emitting LaTeX-style `\boxed{...}` wrappers around numbers in one summary.

Schema validation intentionally does not (and cannot, without much more sophisticated NLP) verify that the prose's claimed direction matches the numbers it cites. This is disclosed here rather than papered over: a local 3B model is a genuine capability ceiling for this kind of numerical narration, and the project's `limitations[]` field exists partly to keep this kind of uncertainty visible to the end user rather than presenting the narrative as authoritative.

## Known quality caveat

`llama3.2:latest` occasionally mixes a raw category code (e.g. `"SE"`) into `chart.x` alongside the human-readable labels it was given (e.g. `"mid-level"`, `"senior-level"`). This passes schema validation (still a list of strings, matching `y`'s length) but isn't a perfectly clean label set — expected variance for a 3B-parameter local model. If chart label fidelity becomes a priority, the fix is to stop trusting the LLM to transcribe `chart.x`/`chart.y` at all and instead have the application overwrite them with the exact `chart_data_by_experience_level` values from `scripts/build_context.py`, keeping only `chart.type` and `chart.title` as LLM-chosen presentation decisions.
