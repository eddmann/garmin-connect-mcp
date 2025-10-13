---
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*)
description: Analyze changes and create a high-quality git commit
---

## Context

- Current branch: !`git branch --show-current`
- Working tree status: !`git status --short --branch`
- Diff (staged + unstaged): !`git diff $(git rev-parse --verify HEAD 2>/dev/null || echo --cached)`
- Recent history (if available): !`git log --oneline -10 || echo "No commits yet"`

## Your task

Analyze the context above and:

1. Summarize the intent of the changes.
2. Create a **concise, conventional commit message** (use [Conventional Commits](https://www.conventionalcommits.org) style if possible).
3. Commit the changes `git commit -m "<generated message>"`.
