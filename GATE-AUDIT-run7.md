# Quality Gate Audit — LibraryHub (run7)

**This run:** `library-hub-testrun5` @ `2288bff` (`main`) · 106 commits · audited 2026-09-04
**Prior runs:** run3 `…testrun` @ `3857b00` · run4 `…testrun2` @ `a3bd6ff` ·
run5 `…testrun3` @ `2aa1da0` · run6 `…testrun4` @ `87fce93`

**Scope:** the swarm workflow, the quality gates that actually run, and the code they produce.
CI is excluded by request.

Figures come from local re-runs of the toolchain, a full-suite run from a clean detached checkout,
and independent mutation runs of the committed configs. Each is labelled.

---

## Verdict

| | run6 (as generated / after fixes) | **run7** |
|---|---|---|
| **Code artifact** | 8.5 / 8.5 | **8.5 / 10** |
| **Workflow & working gates** | 7.5 / 8.5 | **8.0 / 10** |

This run answers the question the last one left open: **which fixes actually survive a fresh run?**

The answer is exact, and it is the most useful result in this report. Everything written into the
**constitution or the framework** propagated. Everything added as a **project file** did not.

| Fixed in run6 | Where it lived | Survived into run7 |
|---|---|---|
| `bandit[sarif]`, `radon` declared | `constitution/engineering.md` rule | ✅ present, SARIF works |
| `GATE_SKIP` budget | `kiln/scheduler/domain/skip_record.py` | ✅ framework code |
| Architect static-analysis step | framework role template | ✅ **new Step 5, propagated** |
| `interrogate fail-under = 90` | `pyproject.toml` | ✅ (also stated in `project.md`) |
| `tests/unit/test_gate_config.py` | project file | ❌ gone |
| `[tool.coverage] fail_under` | project file | ❌ gone |
| `[tool.mypy] files` | project file | ❌ gone |
| `.mutation-scores.json` | project file | ❌ gone |
| `ports.py` mutation exclusion | project file | ❌ gone |
| Portable mutation `test-command` | project file | ❌ regressed |
| Cross-context import contracts | project file | ❌ gone |
| Strict-xfail conftest machinery | project file | ❌ gone (not needed) |

**Four in the durable layer, eight in the disposable one.** The swarm has a memory; it is the
constitution and the framework, and nothing else. That is a clean, actionable law — and it means the
constitution's *content* is now the limiting factor, which finding 1 is about.

The run itself is clean: **466 tests, 0 failures, 0 skips**, verified from a clean detached checkout,
against real Postgres. No spec defects arose. No test-quality defects found.

---

## Baseline Metrics — five runs, local toolchain

| Gate | Command | run3 | run4 | run5 | run6 | **run7** |
|---|---|---|---|---|---|---|
| Type check (bare) | `uv run mypy` | 0 / 50 | fails | fails | 0 / 43 | **fails** ▼ |
| Type check (explicit) | `mypy catalog loans` | — | 0 / 39 | 0 / 55 | 0 / 43 | **0 / 41, strict** |
| Lint | `ruff check` | 0 | 0 | 0 | 0 | **0 findings** |
| Format | `ruff format --check` | — | — | 125 | 118 | **99 files clean** |
| Layering | `lint-imports` | 2 | 4 | 2 `layers` | 4 + cross-ctx | **4 kept** ▼ |
| Complexity | `radon cc -n C` | 0 | 0 | 0 | 0 | **0 above B** |
| Maintainability | `radon mi -n B` | 0 | 0 | 0 | 0 | **all grade A** |
| Doc coverage | `interrogate` | 94.8% | 96.4% | 95.6% | 97.4% | **99.5% (min 90)** ▲ |
| Coverage | `pytest --cov` | 99.13% (**min 90**) | 98.90% | 98.79% | 98.04% | **98.68% (floor 0.0)** |
| SAST | `bandit … -f sarif` | 1 medium | 0 | 0 | 0, works | **0, works** |
| Dependency audit | `pip-audit` | 0 | 0 | 0 | 0 | **0 vulns** |
| Unit | `pytest tests/unit` | 356 | 285 | 287 | 293 | **290** |
| Property | `pytest tests/property` | 61 | 44 | 55 + 1 skip | 59 | **59, 0 skipped** |
| Acceptance | `pytest tests/acceptance` | 150 + **2 FAILED** | 118 (in-mem) | 140 (2 PG) | 148 + 1 xfail (2 PG) | **117 (1 PG)** |
| Clean-checkout run | detached worktree | — | 447 | 482 | 500 | **466 passed** |
| Mutation, catalog | committed config | none | none | 91.67% (scoped) | 90.95% | *(see finding 4)* |
| Mutation, loans | committed config | none | none | none | 91.58% | *(see finding 4)* |

| | run3 | run4 | run5 | run6 | run7 |
|---|---|---|---|---|---|
| Source files | 49 | 39 | 55 | 43 | **41** |
| Infrastructure files | 23 | 12 | 23 | 14 | **11** |
| Statements | 919 | 818 | 916 | 837 | **671** |
| Tests | 569 (2 red) | 447 | 483 | 501 | **466 (0 red)** |
| Persistence | Postgres | `dict` | PG ×2 | PG ×2 | **PG ×1 shared** ▼ |

Clean detached checkout of `2288bff`: **466 passed, 0 failed, 0 skipped.**

---

## What this run did well

### ✅ 1. The specification was consistent by construction

For the first time, no spec defect arose — and not by luck. The specifier chose seed data with **no
overlapping substrings**, which structurally prevents the CAT-1 defect class that cost run3 95 red
commits and that run6 had to contain with a strict xfail:

```gherkin
Given the catalog is seeded with Dune (…, Sci-Fi), Refactoring (…, Software)
      and The Hobbit (…, Fantasy)

  | genre | fantasy | 1 | The Hobbit  |
  | genre | SCI-FI  | 1 | Dune        |
```

run3's and run6's genres were "Science Fiction" and "Computer Science" — where a `Science` filter
under substring matching matches both, contradicting a stated total of 1. "Sci-Fi", "Software" and
"Fantasy" share no substring, so every expected total in the Examples table is satisfiable under the
prose rule. The `title | the | 1 | The Hobbit` row checks out too.

Designing the ambiguity out beats catching it. Worth noting the xfail machinery is therefore
untested this run — it did not propagate, and it was not needed.

### ✅ 2. Architects closed survivors instead of just reporting scores

A real behavioural shift in the handoffs:

```
loan-0 | "killed 15 surviving mutants via new port-contract tests, mutation 0% survival"
loan-1 | "mutation 3.31% survival after killing 30 survivors with new port-contract/
          annotation/immutability/boundary tests"
loan-3 | "Closed loan-3 tie-break test gap … mutation 99.5%"
cat-4  | "mutation 100% on changed modules after adding 2 test fixes"
```

And equivalent mutants are now named rather than absorbed: *"1 true no-op"*, *"12 annotation no-op
survivors"*, *"1 equivalent mutant"*. Previous runs reported a percentage and moved on; this one
treats survivors as work items. That is the mutation gate being used as intended.

### ✅ 3. The event path is exercised across contexts for the first time

Four audits have flagged that `BookReturned` never crossed the context boundary in any test. It now
does. The acceptance conftest gives the catalog and loans apps a **shared broker instance** per
scenario:

```python
@pytest.fixture()
def broker() -> InMemoryBroker:
    """In-process broker shared by the catalog and loans TestClients per scenario."""

def loan_client(postgres_container, broker):
    publisher = RecordingEventPublisher(broker)
    app = create_loans_app(…, publisher=publisher, …)
```

Loans publishes, catalog subscribes, and `tests/acceptance/steps/book_returned_steps.py` drives the
whole path. The transport is still `InMemoryBroker` rather than the declared
`testcontainers[…,rabbitmq]`, so the adapter is unproven — but the *seam* is no longer untested, and
`catalog/infrastructure/broker.py` documents the boundary the RabbitMQ adapter would plug into.

### ✅ 4. Best docstring coverage and cleanest static profile of any run

99.5% against a 90 floor. Zero ruff findings, 99 files formatted, mypy `strict` clean across 41
source files, zero complexity or maintainability warnings, bandit 0 findings with working SARIF
output, pip-audit clean.

### ✅ 5. Evidence integrity holds for the fourth run running

Root tree and all five worktrees clean. 72 handoff messages, **zero** with a non-null `error`. 60
messages carry `Commit:`; all 60 resolve to real commits that are **ancestors of HEAD**.

---

## Findings

### 🔴 1. HIGH — The constitution states a coverage floor that nothing can enforce

`kiln/project/constitution/project.md:176` is the authority on this gate:

```
- Coverage ≥ 90%: `python -m pytest --cov=catalog --cov=loans --cov-report=term-missing`
```

The rule is right and the command cannot enforce it. There is no `--cov-fail-under`, and
`--cov-fail-under` appears **nowhere in the repository** — not in `pyproject.toml`, not in the
constitution, not in CI. Confirmed directly:

```
$ uv run --extra dev python -c "import coverage; print(coverage.Coverage().config.fail_under)"
0.0
```

Coverage is 98.68% today and a drop to 40% would fail nothing. **Six consecutive runs without an
enforced coverage floor** — run3 had one, and it has never come back.

run6 tried to fix this in `pyproject.toml` and the fix did not survive, which is the whole lesson of
this run: the fix belongs in the constitution, where things persist. Change line 176 to include
`--cov-fail-under=90` and the gate becomes real for every future run.

### 🟠 2. HIGH — The constitution prescribes a mutation glob it has already been proven to break on

`project.md:161` gives agents this template:

```toml
excluded-modules = ["catalog/infrastructure/*"]
```

run5's architect diagnosed exactly this and wrote it down at the time: cosmic-ray's
`excluded-modules` subtracts exact path matches, so `catalog/infrastructure/*` matches only the
subdirectories and **silently excludes nothing** — the glob must reach the `.py` files.

The agents got it right anyway this run (`catalog/infrastructure/**/*.py`), so no harm was done. But
the constitution is teaching a known-broken pattern to every future run, and the correction lives
only in a run5 project file that no longer exists.

### 🟠 3. HIGH — The agents ignored the constitution's own portable command

Two lines below the broken glob, `project.md:163` shows the **correct, portable** form:

```toml
test-command = "python -m pytest tests/unit -x -q"
```

What the agents actually committed:

```toml
test-command = "../../.venv/Scripts/python.exe -m pytest tests/unit -x -q"
```

That is Windows-only and depth-dependent. From the repository root it resolves to `C:\projekte\.venv`
— outside the project entirely:

```
$ python -c "import os; print(os.path.abspath('../../.venv'))"
C:\projekte\.venv          # does not exist

$ ls .worktrees/coder/../../.venv
Include  Lib  …            # only works from inside a role worktree
```

So the committed mutation config **cannot be run from the project root**, which is where the
constitution's own instructions run it, and I had to patch it to reproduce any score. This is the
third consecutive run with a machine-specific interpreter path, and the first where the constitution
already contained the right answer and was overridden.

### 🟠 4. HIGH — Mutation reproducibility, and the scoped-vs-committed gap

*(Mutation runs were still executing when this section was written — catalog at 29% showing 1
survivor of 48 completed. Final figures to be appended; the committed configs total **395 mutants**,
165 catalog + 230 loans.)*

The structural problem is unchanged across four runs. Eleven of twelve architect handoffs quote a
score — `mutation 100%`, `3.31% survival`, `94.78%`, `99.2%` — and those come from **scoped** runs
over the files each cycle touched, using configs that are never committed. Only the whole-context
configs are committed, and they are what a re-run measures.

`.mutation-scores.json`, created in run6 to close this, did not survive. There is still no versioned
score, so mutation remains a threshold rather than a ratchet: nothing detects a score that drops
while staying above 80%.

### 🟠 5. MEDIUM — Bounded-context isolation weakened in the acceptance suite

run5 and run6 gave each bounded context its own Postgres container. run7 shares **one**:

```python
@pytest.fixture(scope="session")
def postgres_container():
    """Shared PostgreSQL container for the acceptance session."""

def client(postgres_container, broker):   # catalog  → same container, same dbname
def loan_client(postgres_container, broker):  # loans → same container, same dbname
```

Both fixtures build their URL from the same `container.dbname`. The metadata sets (`Base` vs
`LoansBase`) are disjoint so the tables do not collide, but the two services now share a physical
database in test. The suite no longer demonstrates that the contexts can run against independent
databases — and a stray cross-context foreign key or a table-name collision would pass unnoticed.

For a codebase whose import-linter contracts exist specifically to keep these contexts apart, testing
them against one database is a fidelity regression worth reversing. It is also why acceptance fell
from 148 scenarios to 117 while getting no faster (26.0 s vs 16.7 s).

### 🟡 6. MEDIUM — `uv run mypy` is broken again, and the layering contracts lost their best rule

Two smaller casualties of the same disposable-file problem:

- `[tool.mypy]` has `strict = true` but no `files`, so the bare command a role would naturally run
  errors with *"Missing target module, package, files, or command"*. Only the explicit
  `mypy catalog loans` works (0 issues / 41 files). Fixed in run6; gone again.
- import-linter is back to four same-context contracts. run6's **cross-context isolation** rules —
  `catalog ↛ loans` and `loans ↛ catalog` — are gone. Given finding 5, those are exactly the two
  contracts this run most needed.

### 🟡 7. MEDIUM — The skip budget is implemented but has never fired

`kiln/scheduler/domain/skip_record.py` and `process_next_message.py` survived from run6 and enforce a
budget of 2 consecutive `(gate, reason)` skips. No gate was skipped in this run either — zero
`GATE_SKIP` lines across 72 messages — so the parse → count → refuse chain has now gone two full runs
without executing once. It is the most valuable gate rule in the system and the least proven.

### 🟢 8. LOW — Odds and ends

- `black>=24.0` was added to the dev extras but nothing runs it; formatting is checked with
  `ruff format --check`. Harmless, but it is an undeclared-tool problem in reverse.
- `[tool.setuptools.packages.find]` includes `users*`; there is no `users` package.
- `.kiln/test-baseline.txt` still missing — five runs.
- `reports/` is gitignored and `reports/junit.xml` carries no commit SHA; provenance runs entirely
  through `messages.db`.

---

## Checklist across five runs

| | Target | run3 | run4 | run5 | run6 | run7 |
|---|---|---|---|---|---|---|
| 1 | Acceptance green on HEAD | ❌ 2 red, 95 commits | ✅ | ✅ | ✅ | ✅ **466, 0 skips** |
| 2 | Spec defects caught or avoided | ❌ | n/a | n/a | ✅ caught | ✅ **designed out** |
| 3 | All worktrees clean | ❌ | ✅ | ✅ | ✅ | ✅ |
| 4 | Handoff claims traceable to commits | ❌ | ⚠️ | ⚠️ | ⚠️ | ⚠️ **60/60** |
| 5 | Mutation config committed & portable | ❌ | ❌ | ⚠️ | ✅ | ❌ **regressed** |
| 6 | Mutation scores versioned | ❌ | ❌ | ❌ | ⚠️ | ❌ **gone** |
| 7 | Skip records enforced | ❌ | ❌ | ❌ | ✅ | ✅ **(never fired)** |
| 8 | Coverage floor enforced | ✅ 90 | ❌ | ❌ | ❌ | ❌ **six runs** |
| 9 | Gate tools declared | ✅ | ✅ | ✅ | ✅ | ✅ **constitution rule** |
| 10 | Thresholds survive regeneration | n/a | ❌ | ❌ | ✅ guard test | ❌ **guard gone** |
| 11 | Event path tested across contexts | ❌ | ❌ | ❌ | ❌ | ✅ **in-process broker** |
| 12 | Per-context DB isolation in tests | ✅ | ❌ | ✅ | ✅ | ❌ **shared container** |
| 13 | No test-quality defects | ✅ | ✅ | ❌ 3 | ✅ | ✅ **none found** |

---

## What to do next, in order

**Every item below belongs in `kiln/project/constitution/project.md` or the framework — not in a
project file.** That is the finding this run established, and following it is what makes these fixes
the last time.

1. **Add `--cov-fail-under=90` to the coverage command on `project.md:176`.** One flag, in the one
   place that propagates. Six runs of an unenforced floor ends there. While editing, add
   `files = ["catalog", "loans"]` to the constitution's mypy guidance so the bare command works.

2. **Fix the mutation glob in `project.md:161`** — `["catalog/infrastructure/**/*.py"]`, not
   `["catalog/infrastructure/*"]`. The constitution is currently teaching a pattern that silently
   excludes nothing, already diagnosed once in run5 and lost.

3. **State the `test-command` rule, not just the example.** The constitution shows the portable form
   and the agents wrote an absolute-then-relative Windows path in three consecutive runs. Make it an
   explicit rule — *the interpreter comes from the environment; no `.venv` paths in committed
   configs* — the way the tool-declaration rule was written into `engineering.md`, which is the one
   that stuck.

4. **Put the gate-config guard in the framework.** run6's `tests/unit/test_gate_config.py` was the
   right idea in the wrong place. Ship it from the template so every run gets it, and have it
   interrogate the tools rather than parse the TOML — `coverage.Coverage().config.fail_under >= 90`,
   which is what caught run6's misplaced setting.

5. **Restore per-context database isolation in the acceptance conftest,** and add back the
   cross-context import contracts. The architecture's entire premise is that these two contexts are
   independent; right now nothing tests or enforces that.

6. **Make `.mutation-scores.json` a framework artifact** and fail on a drop rather than only on
   crossing 80%. Then the architects' survivor-killing work — the best behavioural change in this run
   — becomes a visible trend instead of a sentence in a handoff.

7. **Exercise the `GATE_SKIP` path once, deliberately.** Two runs implemented, zero times fired.

8. **Swap `InMemoryBroker` for a RabbitMQ testcontainer in one scenario.** The seam is now wired and
   tested end-to-end; only the transport is unproven. `testcontainers[postgres,rabbitmq]` is already
   a declared dependency.

---

## The code

**8.5 / 10** — the smallest artifact of the five runs, and the cleanest by static measures.

- **99.5% docstring coverage** against a 90 floor, 0 ruff findings, 99 files formatted, mypy `strict`
  clean across 41 source files, zero complexity or maintainability warnings, bandit 0, pip-audit 0.
- **466 tests, zero failures, zero skips, zero xfails**, verified from a clean detached checkout
  against real Postgres. 98.68% coverage over 671 statements.
- **The cross-context event path is tested for the first time** — loans publishes, catalog consumes,
  driven through the acceptance suite.
- **No test-quality defects found**, for the second run running.

Against that, two real regressions: the two bounded contexts now share one database in the acceptance
suite, and the import contracts that kept them apart are gone. The artifact is also noticeably
smaller — 671 statements against run6's 837, 117 acceptance scenarios against 148 — so some of the
cleanliness is a smaller surface rather than better work.

---

## Bottom line

This run settled the open question from run6: **the swarm's memory is the constitution and the
framework, and nothing else.** Four fixes written into those layers came back; eight written into
project files did not. The tool-declaration rule in `engineering.md` is the model — it was stated as
a principle, and `bandit[sarif]` and `radon` have been present ever since.

That makes the constitution's own content the binding constraint, and it currently contains three
defects worth more than any project-level fix: a coverage rule whose command cannot enforce it, a
mutation glob already proven to exclude nothing, and a correct `test-command` example the agents
overrode three runs running.

The workflow itself is in good shape. The specification was consistent by construction rather than by
correction. The architects stopped reporting mutation scores and started closing survivors. The event
seam that four audits flagged is finally exercised. Every gate that runs, passes, from a clean
checkout.

Fix the three lines in `project.md` and the next run starts from a materially better place — which is
now the only kind of fix that lasts.
