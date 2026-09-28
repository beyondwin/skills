
### S1

| Tool | Cost | Time | Human replies | Questions | Confirmed by asking | Right without asking | Wrong assumptions | Missed | Tests | New docs/config | Subagents |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| Baseline (control) | $0.31 | 1.8 min | 4 | 1 | 0 | 8 | 0 | 1 | pass | 1 | 0 |
| superpowers | $3.89 | 17.4 min | 11 | 11 | 9 | 0 | 0 | 0 | pass | 4 | 1 |
| dryforge | $10.19 | 34.5 min | 6 | 20 | 9 | 0 | 0 | 0 | pass | 20 | 10 |
| workflow-orchestrator | $5.23 | 21.9 min | 2 | 6 | 7 | 2 | 0 | 0 | pass | 3 | 6 |
| mattpocock | $4.39 | 16.6 min | 9 | 27 | 9 | 0 | 0 | 0 | pass | 5 | 2 |
| gstack | $35.96 | 116.3 min | 29 | 28 | 9 | 0 | 0 | 0 | pass (pytest)* | 5 | 27 |
| BMAD | $2.93 | 10.4 min | 3 | 5 | 2 | 7 | 0 | 0 | pass | 2 | 4 |
| Spec Kit | $7.58 | 22.7 min | 9 | 11 | 2 | 7 | 0 | 0 | pass | 12 | 0 |
| OpenSpec | $3.48 | 12.7 min | 6 | 5 | 7 | 1 | 0 | 1 | pass | 9 | 0 |
| Ralph | $9.39 | 34.6 min | 2 | 14 | 9 | 0 | 0 | 0 | pass | 11 | 3 |

### S2

| Tool | Cost | Time | Human replies | Questions | Asked about 30/50 conflict | Wrong assumptions | Hidden checks | Tests | git rules | New docs/config | Subagents |
| --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- | ---: | ---: |
| Baseline (control) | $0.27 | 1.9 min | 3 | 3 | yes | F1 | 5/5 | pass | kept | 0 | 0 |
| superpowers | $0.42 | 2.1 min | 5 | 4 | yes | F1 | 5/5 | pass | kept | 0 | 0 |
| dryforge | $4.07 | 12.2 min | 5 | 10 | yes | none | 5/5 | pass | kept | 15 | 5 |
| workflow-orchestrator | $1.64 | 6.2 min | 3 | 6 | yes | none | 5/5 | pass | fixed after correction | 0 | 6 |
| mattpocock | $0.52 | 3.6 min | 4 | 9 | yes | F5 | 2/5 | pass | kept | 1 | 0 |
| gstack | $14.48 | 42.1 min | 19 | 18 | yes | none | 5/5 | pass | kept | 1 | 13 |
| BMAD | $1.99 | 5.6 min | 3 | 4 | yes | none | 5/5 | pass | broken | 2 | 4 |
| Spec Kit | $5.21 | 17.1 min | 13 | 6 | no | none | 5/5 | pass | kept | 12 | 0 |
| OpenSpec | $1.07 | 4.7 min | 6 | 7 | yes | none | 5/5 | pass | kept | 6 | 0 |
| Ralph | $2.13 | 8.5 min | 3 | 12 | yes | none | 5/5 | pass | broken | 9 | 0 |

### S3

| Tool | Cost | Time | Human replies | Questions | Hidden checks | Tests | New docs/config | Subagents | Final location |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- |
| Baseline (control) | $0.13 | 0.7 min | 2 | 1 | 4/4 | pass | 0 | 0 | main |
| superpowers | $0.21 | 0.7 min | 2 | 1 | 4/4 | pass | 0 | 0 | main |
| dryforge | $3.14 | 8.6 min | 4 | 4 | 4/4 | pass | 20 | 5 | main |
| workflow-orchestrator | $0.58 | 2.2 min | 2 | 3 | 4/4 | pass | 0 | 3 | main |
| mattpocock | $0.20 | 1.1 min | 3 | 1 | 4/4 | pass | 1 | 0 | main |
| gstack | $1.73 | 5.7 min | 4 | 2 | 4/4 | pass | 0 | 1 | branch (broke no-push) |
| BMAD | $0.60 | 1.7 min | 1 | 0 | 4/4 | pass | 2 | 1 | main |
| Spec Kit | $0.47 | 2.2 min | 5 | 4 | 4/4 | pass | 4 | 0 | main |
| OpenSpec | $0.66 | 2.1 min | 5 | 1 | 4/4 | pass | 5 | 0 | branch |
| Ralph | $0.89 | 3.8 min | 2 | 9 | 4/4 | pass | 5 | 0 | main |

Totals: agents $123.80, mock user $9.15, judging $7.16, 30 runs
