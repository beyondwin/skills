# Anti-slop skill source audit

Checked 2026-10-09 on macOS. This is source inspection and deterministic
execution, not a model-quality benchmark. The Korean decision record and
multi-angle assessment are in the [learning case](../../learning/cases/2026-10-09-slop-skills-quality.md).

## Sources and attribution boundary

The [Threads post](https://www.threads.com/@homebodify/post/DeOq3GIgGLf)
names four skills without upstream links in the text retrieved. The three
repositories below match the names and mechanisms. The author's installed
revision or fork is unknown. Do not attribute these exact revisions to them.

| Repository | Inspected revision | License read |
| --- | --- | --- |
| [petergyang/no-ai-slop](https://github.com/petergyang/no-ai-slop) | `000650b156983f5159695b441477f4e63b25dc85` | MIT |
| [epoko77-ai/im-not-ai](https://github.com/epoko77-ai/im-not-ai) | `2f3d943d08056b612a92e12bfb72ea94dd2acd18` | MIT |
| [dmmulroy/anti-slop](https://github.com/dmmulroy/anti-slop) | `c44ef22ca116d0ba62a3ff663a0bd13a3f3fa40b` | MIT |

`lagging-concepts` has no verified source: exact-name web searches and GitHub
code search returned no matching implementation on this date. That is a
lookup limit, not proof that the skill does not exist. Its license, execution,
cost, and quality remain unverified.

## Reproduce

Clone the three repositories to a temporary directory, checkout the exact
revisions above, then install anti-slop's locked development dependencies
there with `pnpm install --frozen-lockfile --ignore-scripts`. No global skill
installation is involved. Review the upstream commands before execution.

```bash
/usr/bin/python3 docs/research/2026-10-slop-skill-audit/probe.py /absolute/path/to/checkouts
```

The directory must contain `no-ai-slop/`, `im-not-ai/`, and `anti-slop/`.
The probe checks HEAD and tracked-file cleanliness, executes only local
Python/TypeScript code, and removes its temporary files. It does not run the
upstream live suites, fetch dependencies, or invoke a provider.

Recorded environment: macOS, Python 3.9.6, Node v24.18.0, pnpm 10.33.0.
Dependencies came from anti-slop's lockfile. See [results.json](results.json).

Additional upstream checks executed during this audit:

| Command (inside its checkout) | Result | Scope |
| --- | --- | --- |
| no-ai-slop: `/usr/bin/python3 scripts/build_plugin.py --check` | pass, 1.0.6 archive | Package contents, not editing behavior |
| im-not-ai: `/usr/bin/python3 -m unittest discover -s tests -p test_verify_gates.py -b` | 40/40 pass | Gate logic, not model output |
| anti-slop: `pnpm check` | pass | Lint, 24 test files, TypeScript check, shipped asset equality |

## What the probes establish

- One unchanged Korean control and two deliberately corrupted candidates all
  return gate exit 0. Numeric deletion appears in the report but does not
  fail the gate; negation reversal has no golden or modality finding. This
  demonstrates gate coverage limits, not that the model produces these edits.
- Five lint fixtures confirm detection of a directly typed array pipeline,
  non-detection of an untyped parameter and a type alias, rejection of a
  runtime-valid parser's `unknown` input, and allowance for a type predicate.
  These are rule-policy observations, not a false-positive population estimate.
- Eager and lazy pipelines differ in callback order and sparse-array output.
  The upstream deliberately has no autofix and warns about these semantics.
  These counterexamples support that warning, not a claim of an autofix bug.
- No fresh model calls, comparative human preference test, or authorship
  detection measurement was run. Existing product fixture passes likewise do
  not establish improved writing quality.

The fixtures and probes are newly authored synthetic material. No upstream
source, taxonomy, private text, transcripts, or generated media is vendored.
