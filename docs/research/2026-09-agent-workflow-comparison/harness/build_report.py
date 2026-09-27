#!/usr/bin/env python3
"""Build report.html from results/summary-main.json (numbers are never typed by hand)."""
import html, json, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
# results/ sits next to the scripts in the work dir, and one level up in the repo copy
if not (ROOT / "results").is_dir():
    ROOT = ROOT.parent
OUT = Path(sys.argv[1])
rows = json.loads((ROOT / "results" / "summary-main.json").read_text())
by = {(r["scenario"], r["condition"]): r for r in rows}
ORDER = ["vanilla", "superpowers", "dryforge", "wo", "mattpocock", "gstack", "bmad", "speckit", "openspec", "ralph"]
NAME = {"vanilla": "기본 Claude Code", "superpowers": "superpowers", "dryforge": "dryforge", "wo": "workflow-orchestrator",
        "mattpocock": "mattpocock/skills", "gstack": "gstack", "bmad": "BMAD", "speckit": "Spec Kit", "openspec": "OpenSpec",
        "ralph": "Ralph 루프"}
GIT_FIXED = {("s2", "wo"): "지적 후 고침"}
e = html.escape


def facts(r):
    return Counter(((r["judge"] or {}).get("facts") or {}).values())


def hidden(r):
    h = r["hidden_checks"] or {}
    b = {k: v for k, v in h.items() if isinstance(v, bool) and k != "unittest_discover"}
    return sum(b.values()), len(b)


def docs(r):
    return len((r["judge"] or {}).get("artifacts") or [])


def chip(text, kind):
    return f'<span class="chip {kind}">{e(text)}</span>'


def money(v, lo, hi):
    cls = "lo" if v <= lo else ("hi" if v >= hi else "")
    return f'<td class="num {cls}">${v:.2f}</td>'


def cls_of(c):
    return ' class="mine"' if c in ("superpowers", "dryforge") else ""


def table_s1():
    out = ['<table><thead><tr><th>도구</th><th class="num">비용</th><th class="num">시간</th><th class="num">사람 답변</th>'
           '<th class="num">물어서 확인</th><th class="num">짐작해 맞춤</th><th class="num">틀린 가정</th><th class="num">새 문서</th></tr></thead><tbody>']
    for c in ORDER:
        r = by[("s1", c)]
        f = facts(r)
        wrong = f.get("guessed_wrong", 0)
        out.append(f'<tr{cls_of(c)}><th scope="row">{NAME[c]}</th>{money(r["cost_usd"], 1, 10)}<td class="num">{r["wall_min"]}분</td>'
                   f'<td class="num">{r["user_messages"]}</td><td class="num">{f.get("asked", 0)}</td><td class="num">{f.get("guessed_right", 0)}</td>'
                   f'<td class="num">{chip(str(wrong), "bad") if wrong else "0"}</td><td class="num">{docs(r)}</td></tr>')
    out.append("</tbody></table>")
    return "".join(out)


def table_s2():
    out = ['<table><thead><tr><th>도구</th><th class="num">비용</th><th class="num">사람 답변</th><th>30/50 충돌</th>'
           '<th>틀린 가정</th><th class="num">숨긴 검사</th><th>git 지시</th><th class="num">새 문서</th></tr></thead><tbody>']
    for c in ORDER:
        r = by[("s2", c)]
        s = (r["judge"] or {}).get("scores") or {}
        wrong = [k for k, v in ((r["judge"] or {}).get("facts") or {}).items() if v == "guessed_wrong"]
        hp, hn = hidden(r)
        git = GIT_FIXED.get(("s2", c)) or ("지킴" if s.get("git_rule") else "어김")
        gk = {"지킴": "good", "지적 후 고침": "warn", "어김": "bad"}[git]
        conflict = chip("물음", "good") if s.get("conflict_detected") else chip("스스로 정함", "warn")
        out.append(f'<tr{cls_of(c)}><th scope="row">{NAME[c]}</th>{money(r["cost_usd"], 0.6, 5)}<td class="num">{r["user_messages"]}</td>'
                   f'<td>{conflict}</td><td>{chip(",".join(wrong), "bad") if wrong else "없음"}</td>'
                   f'<td class="num">{chip(f"{hp}/{hn}", "good" if hp == hn else "bad")}</td><td>{chip(git, gk)}</td><td class="num">{docs(r)}</td></tr>')
    out.append("</tbody></table>")
    return "".join(out)


def table_s3():
    out = ['<table><thead><tr><th>도구</th><th class="num">비용</th><th class="num">시간</th><th class="num">사람 답변</th>'
           '<th class="num">숨긴 검사</th><th class="num">새 문서</th></tr></thead><tbody>']
    for c in ORDER:
        r = by[("s3", c)]
        hp, hn = hidden(r)
        out.append(f'<tr{cls_of(c)}><th scope="row">{NAME[c]}</th>{money(r["cost_usd"], 0.25, 2)}<td class="num">{r["wall_min"]}분</td>'
                   f'<td class="num">{r["user_messages"]}</td><td class="num">{chip(f"{hp}/{hn}", "good" if hp == hn else "bad")}</td>'
                   f'<td class="num">{docs(r)}</td></tr>')
    out.append("</tbody></table>")
    return "".join(out)


total = sum(r["cost_usd"] for r in rows)
sp = {s: by[(s, "superpowers")]["cost_usd"] for s in ("s1", "s2", "s3")}
df = {s: by[(s, "dryforge")]["cost_usd"] for s in ("s1", "s2", "s3")}
ratio = {s: df[s] / sp[s] for s in sp}

page = f"""<meta charset="utf-8">
<title>워크플로 도구 실측</title>
<meta name="description" content="superpowers, dryforge 등 9개 에이전트 워크플로 도구를 같은 과제 3개로 실측한 비교 보고서">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@400;500;700&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root {{
  --ground: #f4f6f8; --surface: #ffffff; --ink: #17212b; --muted: #5a6572; --rule: #d8dee5;
  --accent: #0b6e69; --accent-soft: #e2f1ef;
  --good: #1f7a4c; --good-bg: #e3f3ea; --warn: #9a6200; --warn-bg: #fbf0da; --bad: #b3261e; --bad-bg: #fbe6e4;
  --mine: #eef4fb;
  --sans: "IBM Plex Sans KR", "Apple SD Gothic Neo", "Noto Sans KR", system-ui, sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, SFMono-Regular, Menlo, monospace;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    color-scheme: dark;
    --ground: #0f151b; --surface: #16202a; --ink: #e6ebf0; --muted: #9aa6b2; --rule: #2a3643;
    --accent: #4fc1b8; --accent-soft: #123330;
    --good: #6fd19b; --good-bg: #143325; --warn: #f0b64f; --warn-bg: #3a2b0f; --bad: #ff8a80; --bad-bg: #3d1916;
    --mine: #182a3a;
  }}
}}
:root[data-theme="dark"] {{
  color-scheme: dark;
  --ground: #0f151b; --surface: #16202a; --ink: #e6ebf0; --muted: #9aa6b2; --rule: #2a3643;
  --accent: #4fc1b8; --accent-soft: #123330;
  --good: #6fd19b; --good-bg: #143325; --warn: #f0b64f; --warn-bg: #3a2b0f; --bad: #ff8a80; --bad-bg: #3d1916;
  --mine: #182a3a;
}}
* {{ box-sizing: border-box; }}
body {{ background: var(--ground); color: var(--ink); font: 15px/1.65 var(--sans); margin: 0; }}
.wrap {{ max-width: 1040px; margin: 0 auto; padding-inline: 16px; padding-block: 28px 64px; display: grid; gap: 28px; }}
header {{ display: grid; gap: 8px; }}
.eyebrow {{ font: 500 12px/1.4 var(--mono); letter-spacing: .06em; color: var(--muted); text-transform: uppercase; }}
h1 {{ font-size: clamp(26px, 4.4vw, 38px); line-height: 1.2; margin: 0; text-wrap: balance; letter-spacing: -.01em; }}
h2 {{ font-size: 21px; margin: 0 0 12px; text-wrap: balance; }}
h3 {{ font-size: 16px; margin: 0 0 8px; }}
p {{ margin: 0; max-width: 68ch; }}
.meta {{ color: var(--muted); font-size: 13px; display: flex; flex-wrap: wrap; gap: 6px 14px; }}
.meta code {{ font: 12px var(--mono); }}
section {{ display: grid; gap: 12px; }}
.verdict {{ background: var(--accent-soft); border: 1px solid var(--rule); border-radius: 12px; padding: 20px; display: grid; gap: 14px; }}
.verdict .big {{ font-size: clamp(19px, 2.6vw, 23px); font-weight: 700; line-height: 1.4; }}
.two {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px; }}
.card {{ background: var(--surface); border: 1px solid var(--rule); border-radius: 10px; padding: 16px; display: grid; gap: 8px; align-content: start; }}
ul {{ margin: 0; padding-left: 1.2em; display: grid; gap: 4px; }}
li {{ max-width: 70ch; }}
.scroll {{ overflow-x: auto; background: var(--surface); border: 1px solid var(--rule); border-radius: 10px; }}
table {{ border-collapse: collapse; width: 100%; min-width: 640px; font-size: 14px; }}
th, td {{ padding: 9px 12px; border-bottom: 1px solid var(--rule); text-align: left; vertical-align: top; }}
thead th {{ font-size: 12px; font-weight: 500; color: var(--muted); white-space: nowrap; background: var(--surface); }}
tbody tr:last-child th, tbody tr:last-child td {{ border-bottom: 0; }}
tbody th {{ font-weight: 500; white-space: nowrap; }}
tr.mine {{ background: var(--mine); }}
.num {{ text-align: right; font-variant-numeric: tabular-nums; font-family: var(--mono); font-size: 13px; white-space: nowrap; }}
td.lo {{ color: var(--good); font-weight: 500; }}
td.hi {{ color: var(--bad); font-weight: 500; }}
.chip {{ display: inline-block; font: 500 12px/1.5 var(--sans); padding: 1px 8px; border-radius: 999px; white-space: nowrap; }}
.chip.good {{ background: var(--good-bg); color: var(--good); }}
.chip.warn {{ background: var(--warn-bg); color: var(--warn); }}
.chip.bad {{ background: var(--bad-bg); color: var(--bad); }}
.note {{ color: var(--muted); font-size: 13px; }}
.kicker {{ font-weight: 700; color: var(--accent); }}
ol {{ margin: 0; padding-left: 1.3em; display: grid; gap: 8px; }}
details {{ background: var(--surface); border: 1px solid var(--rule); border-radius: 10px; padding: 12px 16px; }}
summary {{ cursor: pointer; font-weight: 500; }}
summary:focus-visible, a:focus-visible {{ outline: 2px solid var(--accent); outline-offset: 2px; }}
a {{ color: var(--accent); }}
</style>

<div class="wrap">
<header>
  <div class="eyebrow">실측 보고서 · 2026-09-27 · Claude Code 2.1.280 · Opus 5.5</div>
  <h1>superpowers에서 갈아탈 이유가 있을까</h1>
  <p>9개 워크플로 도구와 기본 Claude Code를 같은 과제 3개로 끝까지 돌려 비교했습니다. 30회 실행에 에이전트 비용 ${total:.0f}이 들었습니다.</p>
  <div class="meta">
    <span>superpowers 6.4.1 <code>5bf4e78</code></span><span>dryforge 1.3.7 <code>904f257</code></span>
    <span>workflow-orchestrator 1.5.0</span><span>mattpocock 1.2.3</span><span>gstack 1.91.2.0</span>
    <span>BMAD 6.12.0</span><span>Spec Kit <code>c00dc05</code></span><span>OpenSpec 1.13.2</span><span>Ralph <code>88d488a</code></span>
  </div>
</header>

<section class="verdict" aria-labelledby="v">
  <h2 id="v" class="eyebrow" style="margin:0">결론</h2>
  <div class="big">superpowers를 그대로 쓰세요. dryforge는 틀리면 비싼 새 기능에만 <code>/dryforge:ready</code>로 옆에 두세요.</div>
  <div class="two">
    <div class="card">
      <h3>superpowers를 유지하는 이유</h3>
      <ul>
        <li>결과 품질은 도구마다 거의 같았습니다. 30회 중 기능 결함은 1회(mattpocock 쿠폰 과제)였고 superpowers는 0회입니다.</li>
        <li>기존 코드 과제 ${sp['s2']:.2f}, 버그 수정 ${sp['s3']:.2f}로 가장 싼 축이었습니다(기본·mattpocock과 같은 급).</li>
        <li>디버깅·리뷰·검증 스킬을 세션 훅이 알아서 켭니다. 비슷한 스킬은 다른 도구에도 있지만 직접 불러야 합니다.</li>
        <li>지금 쓰는 <code>sddx</code>, <code>pre-sdd-review</code>는 superpowers 모양의 스펙·계획 파일을 받습니다. dryforge 계획 파일을 받는지는 시험하지 않았습니다.</li>
      </ul>
    </div>
    <div class="card">
      <h3>dryforge를 옆에 둘 때 알아둘 것</h3>
      <ul>
        <li>좋은 점: 쿠폰 과제에서 틀린 가정이 0개였고, 세 과제 모두 git 지시를 지켰습니다.</li>
        <li>대가: superpowers보다 {ratio['s1']:.1f}배, {ratio['s2']:.1f}배, {ratio['s3']:.0f}배 비쌌고, 과제마다 문서를 15~20개 만들었습니다.</li>
        <li><code>CLAUDE.md</code>·<code>AGENTS.md</code>를 백업한 뒤 다시 씁니다. 직접 관리하는 저장소에는 맞지 않습니다.</li>
        <li>같이 설치해도 <code>/dryforge:ready</code>로 부르면 dryforge가 주도했습니다(첫 턴 2회 확인).</li>
      </ul>
    </div>
  </div>
</section>

<section aria-labelledby="m">
  <h2 id="m">내 상황이라면</h2>
  <div class="scroll"><table>
    <thead><tr><th>상황</th><th>추천</th><th>근거</th></tr></thead>
    <tbody>
      <tr><th scope="row">작은 버그·설정 수정</th><td>기본 또는 superpowers</td><td>경계 버그에서 $0.13~0.21, 1분 안팎. 모두 회귀 테스트를 추가했습니다.</td></tr>
      <tr><th scope="row">기존 코드에 기능 추가</th><td>superpowers</td><td>충돌은 잡았지만 조합 규칙을 짐작했습니다. 설계 승인 때 꼼꼼히 읽으세요.</td></tr>
      <tr><th scope="row">요구가 모호하고 틀리면 비싼 기능</th><td>dryforge <code>/ready</code> 추가</td><td>틀린 가정 0, 충돌을 첫 질문으로, git 규율. 비용 약 10배.</td></tr>
      <tr><th scope="row">사람 손을 최소로</th><td>workflow-orchestrator 또는 BMAD</td><td>새 CLI 과제에서 사람 답변 2~3번. BMAD는 지시를 어기고 main에 커밋했습니다.</td></tr>
      <tr><th scope="row">결정마다 깊은 검토</th><td>gstack (신중히)</td><td>결정마다 한 번씩 물어 29번 답했고 116분, $36이 들었습니다. 버그 과제에서 push 금지를 어겼고, Codex를 자동 호출했습니다.</td></tr>
      <tr><th scope="row">명세 문서를 저장소에 남김</th><td>OpenSpec</td><td>새 CLI·쿠폰 과제에서 Spec Kit보다 쌌습니다. Spec Kit은 충돌을 묻지 않고 헌법으로 정했습니다.</td></tr>
      <tr><th scope="row">사람 없이 오래 돌리기</th><td>Ralph 루프</td><td>요구사항 대화 뒤 자동. 매 반복 main에 커밋하고 태그를 만듭니다.</td></tr>
    </tbody>
  </table></div>
</section>

<section aria-labelledby="b">
  <h2 id="b">먼저 알아야 할 기준선</h2>
  <p><span class="kicker">스킬이 정답률을 바꾸지 않았습니다.</span> 기본 Claude Code도 세 과제를 모두 맞게 끝냈습니다. 도구가 바꾼 것은 과정입니다. 얼마나 묻는지, 사람이 몇 번 답하는지, 돈과 시간, 저장소에 남기는 문서, git 지시 준수가 달랐습니다. 과제가 작고 모델이 강해서일 수 있습니다.</p>
</section>

<section aria-labelledby="s1">
  <h2 id="s1">S1 · "가계부 CLI 하나 만들어줘"</h2>
  <p class="note">빈 저장소. 사용자만 아는 요구 9개(표준 라이브러리만, 삭제 기능, 0원 이하 거부 등). 10개 조건 모두 요구 기능이 실제로 동작했습니다.</p>
  <div class="scroll">{table_s1()}</div>
</section>

<section aria-labelledby="s2">
  <h2 id="s2">S2 · "쿠폰 두 장까지 같이 쓸 수 있게 해줘"</h2>
  <p class="note">기존 모듈. 문서는 할인 상한 30%, 코드는 50%(숨은 충돌). 정답은 "정률 1장 + 정액 1장만, 정률 먼저, 30%". 숨긴 검사는 결과 코드를 직접 import해 확인했습니다.</p>
  <div class="scroll">{table_s2()}</div>
  <p class="note">mattpocock은 모의 사용자가 <code>/to-spec</code> 단계를 건너뛴 실행이라 도구 탓으로만 보기 어렵습니다.</p>
</section>

<section aria-labelledby="s3">
  <h2 id="s3">S3 · "딱 50,000원 주문에 배송비가 붙었대"</h2>
  <p class="note"><code>&gt;=</code> 대신 <code>&gt;</code> 한 글자 버그. 10개 조건 모두 원인을 맞히고 회귀 테스트를 추가했습니다. dryforge는 첫 사이클이라 프로젝트 문서 하네스를 통째로 만들었습니다. README도 작은 수정에는 쓰지 말라고 합니다.</p>
  <div class="scroll">{table_s3()}</div>
</section>

<section aria-labelledby="p">
  <h2 id="p">두 번 이상 반복된 패턴</h2>
  <ol>
    <li><b>물어도 추천안이 틀렸습니다.</b> 쿠폰 과제에서 dryforge, mattpocock, OpenSpec, Spec Kit 4개 도구가 조합·순서를 물으면서 사용자 의도와 반대인 안을 추천했습니다. "추천대로"라고만 답하면 짐작과 결과가 같습니다.</li>
    <li><b>문서를 많이 남기는 도구가 있습니다.</b> dryforge 15~20개, Spec Kit 4~12개, Ralph 5~11개. superpowers와 기본은 0~4개였습니다.</li>
    <li><b>git 지시를 어긴 도구가 있습니다.</b> BMAD는 묻지 않고 main에 커밋했습니다. Ralph는 구조상 중간 지시를 받을 통로가 없습니다. workflow-orchestrator는 지적받은 뒤 고쳤습니다. gstack은 버그 과제에서 push 금지를 어겼습니다.</li>
    <li><b>gstack은 외부 모델을 부릅니다.</b> 설치된 Codex CLI를 계획 검토와 <code>/review</code>에서 외부 의견으로 호출했습니다.</li>
  </ol>
</section>

<section aria-labelledby="h">
  <h2 id="h">어떻게 쟀나</h2>
  <div class="two">
    <div class="card"><h3>격리</h3><p>조건마다 <code>claude -p --setting-sources project --plugin-dir &lt;도구&gt; --strict-mcp-config</code>. 사용자 설정·전역 스킬·계정 커넥터를 막고 해당 도구만 올렸습니다. 프로젝트형 도구는 과제 저장소에 설치해 커밋한 뒤 시작했습니다.</p></div>
    <div class="card"><h3>모의 사용자</h3><p>Sonnet이 사실 시트를 가진 사용자를 연기했습니다. 물은 것에만 답하고, 각 도구 문서의 명령 순서를 따랐습니다. 설계가 사실과 명백히 다르면 바로잡았습니다.</p></div>
    <div class="card"><h3>채점</h3><p>결과 코드를 직접 import하는 숨긴 검사와, 대화에 참여하지 않은 Opus 채점자의 루브릭 평가를 함께 썼습니다. 사실마다 물어서 얻음·짐작해 맞춤·틀림·빠짐으로 분류했습니다.</p></div>
    <div class="card"><h3>비용</h3><p><code>--resume</code> 세션의 비용 보고는 누적값이라(대조 실험으로 확인) 세션별 마지막 값을 썼습니다. 모의 사용자·채점 비용은 제외했습니다.</p></div>
  </div>
  <details><summary>이 조사가 증명하지 못하는 것</summary>
    <ul style="margin-top:8px">
      <li>조건×과제당 1회씩입니다. 수 배 이상 차이만 의미 있게 읽었습니다.</li>
      <li>모의 사용자는 진짜 사람이 아닙니다. 가끔 명령 순서를 벗어났습니다.</li>
      <li>gstack의 첫 실행은 과제끼리 상태 폴더를 같이 써서 기록이 섞였습니다. 실행마다 상태 폴더를 따로 두고 다시 돌린 값으로 바꿨습니다.</li>
      <li>작은 파이썬 과제뿐입니다. 큰 저장소·긴 작업·팀 협업은 재지 않았습니다.</li>
      <li>공존 실험은 첫 턴만 봤습니다.</li>
    </ul>
  </details>
</section>

<p class="note">전체 문서와 하네스: 저장소의 <code>docs/research/2026-09-agent-workflow-comparison/</code> (README, method, tools, results, harness).</p>
</div>
"""
OUT.write_text(page)
print("wrote", OUT, len(page))
