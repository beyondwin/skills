# Writing the page

Apply these to every sentence on the page: prose, table cells, and captions. Code tokens
(paths, fields, codes, enum values, headers) stay exactly as read.

## Every language

- A table cell holds at most two short sentences. Put a list of conditions in its own rows,
  and put what the caller does in Handling.
- One fact per sentence. Split a sentence that joins two facts with "and" or a comma.
- At most one parenthetical per sentence. If the aside matters, give it a sentence or a
  column; if it does not, drop it.
- Use the words the reader's team uses: the words in the user's request, the consumer code,
  or the contract file. Do not copy this skill's working words onto the page: envelope, row,
  caller, card.
- Say when, not "may". Replace "can be null" or "may fail" with the condition from the code.
  Keep "may" only for what the server cannot know, and say what it cannot see.
- The lede is at most three sentences.

## Korean pages

- One register. Prose uses 합니다체. A table cell is either a short noun phrase or 합니다체,
  the same choice for the whole page. Never 한다체 ("다시 부른다").
- Use the Korean words a developer team uses, or the English term when that is what the team
  writes. Do not translate this skill's words literally.

| Instead of | Write |
| --- | --- |
| 응답 봉투 | 공통 응답 형식 |
| 부른 사람 | 호출한 사용자 |
| 내보내기 줄 | 내보내기 항목 |
| 재시도 버튼을 보인다 | 재시도 버튼을 보여 줍니다 |
| `fileUrl` 은 null 일 수 있습니다 | `fileUrl` 은 `DONE` 일 때만 옵니다 |
| 실패(서버가 처리하지 못한 오류, 본문 형식 다름) | 서버가 처리하지 못한 오류입니다. 본문 형식이 다릅니다 |
