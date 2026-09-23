# prlab-review-tests

Pass/fail tests for PR review tools on the cricket scoring estate.

Product repositories stay blind. This repo owns the cases, the code-only patches, the PR generator, and the scorers. A product PR must not mention traps, hops, or this harness.

## Isolation

During a Greptile run, the only allowed bot commenter is `greptile-apps[bot]`. The runner account posts one `@greptileai` comment and nothing else. Cursor, Bugbot, and other review tools stay off these PRs until we add cases for them — then those bots may comment too.

Do not mention this repo, `TRAPS.md`, hop numbers, or expected findings in a product PR title, body, or commit message.

## Two named Greptile tests

| Test | What the bot sees | How it is set |
|---|---|---|
| `greptile-cold` | One repo, no cluster | Protocol PR has no `greptile.json` |
| `greptile-cluster` | Protocol plus named siblings | Same protocol patch plus `greptile.json` `context.repos` for scoring, stats, and fantasy |

Every other case is single-repo and is scored under `greptile-cold`.

## Layout

```
cases/cases.json     # pass/fail expectations
patches/             # code-only diffs against product main
scripts/generate_prs.py
scripts/score_greptile.py
```

## Generate PRs (does not trigger a bot)

From this directory, with the eleven product clones as siblings:

```bash
python3 scripts/generate_prs.py
```

That opens one PR per case on `eval/<id>` and leaves it open. Inspect the diffs. Then, after Greptile is reconnected to the product remotes:

```bash
python3 scripts/generate_prs.py --trigger-greptile
```

`--trigger-greptile` posts `@greptileai` from the runner account. Omit it until you have checked the PRs.

## Score

```bash
python3 scripts/score_greptile.py
```

A case passes when `greptile-apps[bot]` comments match every `must_flag` regex. Isolation fails if anyone else comments before you opt a second tool in.

## Product remotes

`srajat-leap/prlab-cricket-*` — public. This harness is `srajat-leap/prlab-review-tests`.
