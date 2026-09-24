# prlab-review-tests

Pass/fail tests for PR review tools on the cricket scoring estate.

Cases describe a product change and the **claim** a review must assert. They are not tied to a vendor. Each tool is a plugin: trigger text, bot login, and optional cluster config.

Every case id starts with `test-` and names the intent (`test-stats-not-out-display-increments-wickets`). `intent` is the one-line goal. `tests` is the cricket trap.

Review-tool skills live in `cases/capabilities.json`. A case points at one or more ids (`"capability": "contract-leak"` or `"capabilities": ["contract-leak", "leak-propagation"]`). The same skill can be reused across cases and later tools. Ids name what the review product can do (cross-repo impact, omitted guard as true), not design principles or cricket-specific bug labels.

Product repositories stay blind. A product PR must not mention this harness, hop numbers, or expected findings.

## Layout

```
cases/capabilities.json   # shared review-tool skills (referenced by id)
cases/cases.json          # shared traps (`capability` is a catalog id)
patches/                  # code-only diffs
src/prlab_eval/tools/     # one module per review product
tests/unit/               # matcher and case tests
tests/eval/               # live setup → execute → assert
reports/                  # written by pytest
```

## Contexts

| Context | What the tool sees |
|---|---|
| `single-repo` | The PR repo only |
| `cluster` | The PR repo plus `cluster_repos` (protocol → scoring, stats, fantasy) |

`--tool` selects the plugin (trigger, bot, cluster context). Cases and capabilities stay shared.

| Column | Meaning |
|---|---|
| Capability | The review-tool skill this case measures. Reports also roll up P/R by capability. |
| Expected finding | The trap. What a correct review must mean. |
| Actual PR comment | The tool's GitHub comment(s), not the judge. |
| Judge verdict | Whether those comments assert the expected finding, plus a short reason. |
| Judge evidence | Substring the judge copied from the comment. |
| Recall | Expected findings asserted / expected findings. |
| Precision | PR comments that support an asserted finding / all PR comments. Extra nits lower precision. |
| Isolation | Process check. Only the selected tool's bot may review. Use `--allow-bots` to opt another bot in. |
| Context | What the tool was allowed to see. |
| Tokens | Diagnostic keyword check. Not used for pass/fail. |

## Install

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

## Tests

Case **data** lives in `cases/cases.json`. Each case is one pytest node:

```
tests/eval/test_reviews.py::test_review_tool_flags_regression[test-stats-not-out-display-increments-wickets] FAILED
```

Do not write one hand-copied test function per trap. Add a JSON case; pytest picks it up.

```bash
pytest                    # unit tests
pytest tests/eval --run-eval --tool greptile --judge-provider gemini --cleanup
```

## Eval a tool (live GitHub)

1. **Setup** — open eval PRs. Creates each `eval/*` branch if it is missing (after cleanup, for example):

```bash
python3 -m prlab_eval setup
```

2. **Trigger** — mention the tool once per open eval PR. Skips PRs that already have the mention:

```bash
python3 -m prlab_eval trigger --tool greptile
```

3. **Execute + assert** — collect comments and score claims with a temperature-0 judge. You do not need an OpenAI key. Add `--wait` if reviews are still landing. Add `--cleanup` to close the eval PRs and delete their branches after the report is written.

4. **Cleanup** — close leftover eval PRs and delete `eval/*` branches without scoring. Reports stay.

```bash
python3 -m prlab_eval cleanup
# or: python3 scripts/cleanup_prs.py
```

Free judge options (first match wins if you set nothing):

| Provider | Cost | Setup |
|---|---|---|
| **Groq** | Free tier | [console.groq.com](https://console.groq.com) → `export GROQ_API_KEY=...` |
| **Gemini** | Free tier | [aistudio.google.com](https://aistudio.google.com) → `export GEMINI_API_KEY=...` |
| **Ollama** | Local, free | `ollama pull llama3.2` then `--judge-provider ollama` |
| **GitHub Models** | Free with `gh` | `gh auth login` then `--judge-provider github` |

```bash
export GROQ_API_KEY=...
# default Groq model is openai/gpt-oss-120b
pytest tests/eval --run-eval --tool greptile --judge-provider groq --cleanup

# or Qwen 3.8 27B
pytest tests/eval --run-eval --tool greptile --judge-provider groq --judge-model qwen/qwen3.8-27b --cleanup
```

Eval pings the judge once before any case. A bad key or model stops the session immediately.

```bash
python3 -m prlab_eval judge-check --provider openai
```

`--trigger` on pytest still works as a one-shot. It uses the same skip-if-already-mentioned check. Prefer the separate `trigger` command so you can inspect the comments before scoring.

Reports written under `reports/`:

- `latest.md` / `latest.json` — one row per case
- `report.html` — pytest-html (self-contained)

## Add a tool

1. Create `src/prlab_eval/tools/<name>.py` with `name`, `bot_logins`, `trigger_body`, `context_files`, `collect`, and `trigger`.
2. Register it in `src/prlab_eval/tools/__init__.py`.
3. Run `pytest tests/eval --run-eval --tool <name>`.

Cases do not change.

## Isolation

The runner account may post the tool's trigger comment. Unexpected `[bot]` logins fail isolation unless listed in `--allow-bots`. Leave Cursor and other reviewers off a run until you opt them in.

## Product remotes

`srajat-leap/prlab-cricket-*`. This harness is `srajat-leap/prlab-review-tests`.
