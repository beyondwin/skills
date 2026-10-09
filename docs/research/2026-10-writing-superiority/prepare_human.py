#!/usr/bin/env python3
"""Create a private, unscored personal preference sheet; never sends answers."""
import argparse
import html
import json
import re
from pathlib import Path
import run


def inline(s):
 s=html.escape(s)
 s=re.sub(r'`([^`]+)`',r'<code>\1</code>',s)
 s=re.sub(r'\*\*([^*]+)\*\*',r'<strong>\1</strong>',s)
 s=re.sub(r'\[([^\]]+)\]\([^)]*\)',r'\1',s)
 return s


def markdown(s):
 lines=s.splitlines();out=[];i=0
 while i<len(lines):
  line=lines[i].strip()
  if not line:i+=1;continue
  if line.startswith('```'):
   block=[];i+=1
   while i<len(lines) and not lines[i].strip().startswith('```'):block.append(lines[i]);i+=1
   out.append('<pre><code>'+html.escape('\n'.join(block))+'</code></pre>');i+=1;continue
  if line.startswith('|'):
   rows=[]
   while i<len(lines) and lines[i].strip().startswith('|'):
    text=lines[i].strip()
    if not re.fullmatch(r'[| :\-]+',text):rows.append([inline(x.strip()) for x in text.strip('|').split('|')])
    i+=1
   out.append('<table>'+''.join('<tr>'+''.join('<td>'+x+'</td>' for x in row)+'</tr>' for row in rows)+'</table>');continue
  m=re.match(r'^(#{1,6})\s+(.*)',line)
  if m:out.append('<h3>'+inline(m.group(2))+'</h3>');i+=1;continue
  m=re.match(r'^(?:[-*]|\d+[.])\s+(.*)',line)
  if m:
   indent=len(lines[i])-len(lines[i].lstrip())
   out.append('<p class="item" style="margin-left:'+str(indent//2)+'em">'+inline(line)+'</p>');i+=1;continue
  para=[line];i+=1
  while i<len(lines) and lines[i].strip() and not re.match(r'^(?:#|```|\||[-*] |\d+[.] )',lines[i].strip()):para.append(lines[i].strip());i+=1
  out.append('<p>'+inline(' '.join(para))+'</p>')
 return '\n'.join(out)


def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('archive',type=Path)
 args=ap.parse_args();root=args.archive
 cases=json.loads((run.ROOT/'cases.json').read_text());parts=[];mapping={};hashes={}
 # Development aid, selected by host and genre. Not part of the frozen experiment.
 for number,index in enumerate([0,6,10],1):
  c=cases[index];arms=['baseline','previous'] if number%2 else ['previous','baseline']
  mapping[str(number)]=dict(zip('AB',arms));drafts=[]
  for label,arm in mapping[str(number)].items():
   text=run.masked(root,c,arm)
   hashes[str(number)+label]=run.h.digest(root/(c['id']+'--'+arm)/'response.txt')
   drafts.append('<article><h2>글 '+label+'</h2>'+markdown(text)+'</article>')
  parts.append('<section><h2>'+str(number)+'. '+html.escape(c['prompt'])+'</h2><div class="pair">'+''.join(drafts)+'</div><fieldset><legend>더 읽기 편한 글</legend>'+''.join('<label><input type="radio" name="q'+str(number)+'" value="'+v+'">'+v+'</label>' for v in ['A','B','차이 없음'])+'</fieldset><textarea id="note'+str(number)+'" placeholder="헷갈린 문장이나 선택 이유가 있으면 적어주세요."></textarea></section>')
 page='''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>익명 글 비교</title><style>
body{font:17px/1.8 system-ui,sans-serif;margin:32px auto;padding:0 24px;max-width:1440px;color:#20282d;background:#f8fafb}h1{font-size:30px}h2{font-size:21px}h3{font-size:18px;margin-top:1.7em}.pair{display:grid;grid-template-columns:1fr 1fr;gap:24px}article{background:white;padding:24px;border:1px solid #dce2e6;border-radius:12px;min-width:0}section{margin:40px 0 64px}code{font-size:.88em;background:#f1f4f6;overflow-wrap:anywhere}pre{white-space:pre-wrap;background:#f1f4f6;padding:12px}table{border-collapse:collapse;font-size:14px;line-height:1.6;width:100%}td{border:1px solid #dce2e6;padding:8px}tr:first-child{font-weight:bold;background:#f1f4f6}.item{padding-left:12px}fieldset{margin:20px 0;border:0;padding:0}label{margin-right:24px}textarea{width:100%;box-sizing:border-box;min-height:70px;font:inherit;padding:10px}button{font:inherit;padding:10px 20px;background:#155d70;color:white;border:0;border-radius:8px;cursor:pointer}#result{white-space:pre-wrap}small{display:block;color:#52616a}@media(max-width:850px){.pair{grid-template-columns:1fr}body{padding:0 12px}article{padding:18px}}
</style><h1>어느 글이 더 읽기 편한가요?</h1><p>세 쌍을 읽고 A·B·차이 없음 중 하나를 골라주세요. 짧은 글을 고를 필요는 없습니다. 원인과 조건, 다음 행동을 덜 되읽고 이해할 수 있는 쪽을 고르면 됩니다.</p><small>개인 취향을 확인하기 위한 자료입니다. 선택은 자동으로 전송되거나 저장되지 않습니다. 글의 출처와 작성 방법은 가렸습니다. 링크는 표시 문구만 남겼으며 글의 내용은 바꾸지 않았습니다.</small>'''+''.join(parts)+r'''<button onclick="collect()">답변 모으기</button><pre id="result"></pre><script>function collect(){let a=[];for(let i=1;i<=3;i++){let c=document.querySelector('input[name=q'+i+']:checked');let n=document.getElementById('note'+i).value;a.push(i+': '+(c?c.value:'미선택')+(n?' — '+n:''))}document.getElementById('result').textContent=a.join('\n')+'\n\n이 내용을 채팅에 붙여 넣어 주세요.'}</script></html>'''
 path=root/'human-reading.html';path.write_text(page)
 run.dump(root/'human-reading-mapping.json',{'mapping':mapping,'source_response_hashes':hashes,'sheet_sha256':run.h.digest(path),'purpose':'Personal preference elicitation only. Post-hoc selected cases, one per host spanning explanations and handoffs. Not an independent human benchmark or superiority confirmation.'})
 print(str(path))

if __name__=='__main__':main()
