# Commit messages and PR descriptions

## Establish the comparison

For a staged commit message, inspect the index against HEAD, not the whole working
tree. Start with `git status --short`, then inspect
`git -c diff.ignoreSubmodules=none diff --cached --no-ext-diff --no-textconv --submodule=short`.
Use `--stat` or `--name-status` to orient yourself, not as a substitute for content.
An empty index means no staged change; do not substitute unstaged files.

For a PR, resolve the requested base and inspect the merge-base comparison to HEAD.
Separate that committed range from local staged/unstaged work. If the base is
missing or ambiguous, say what remains unresolved rather than guessing a branch.

Binary files and submodule pointers are changes even without ordinary text hunks.
A pointer change does not establish the behavior inside the referenced repository.
Read relevant nearby code only to understand the changed behavior; unchanged context
does not become part of the change description.

## Write the message

Honor local language and message conventions. Explain the concrete trigger and
resulting behavior; add the reason if evidence supports it. Scale the detail to the
change. A small commit may need only a title. PR descriptions may need validation
and a remaining limitation. Report tests from observed results, with their scope;
do not run a suite merely to write a message unless the request includes verification.

Do not mention unrelated edits or unchanged settings just because they appear in
context lines. Reading a test definition proves that it exists, not that it passed.
Do not claim an operational rollout from a merge, file edit or local test.

Return only the requested text when asked for a message. Do not stage, commit,
push, open a PR or send the draft unless the user separately authorized that action.
