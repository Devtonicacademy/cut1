---
description: Shift handoff briefing - what changed since the last update
argument-hint: "[window, e.g. 8h | 2d | since-last-commit]"
allowed-tools: Bash(git:*), mcp__github__*, mcp__Railway__*, mcp__Supabase__*
---

Brief me for the start of my shift on `devtonicacademy/cut1`. Keep it short and scannable.

## 1. Pick the time window
- If `$ARGUMENTS` is given (e.g. `8h`, `2d`), use that.
- Otherwise use the most recent interval: the time of the latest commit by the current git user (`git log --author="$(git config user.email)" -1 --format=%cI`), or if none, the previous session's last activity. Fall back to 24h if neither can be found.
- State the window you chose in the first line.

## 2. Gather (run independent calls in parallel)
- **Git:** `git fetch --all --prune`, then commits in the window across all branches (`git log --all --since=<window> --format='%h %an %s (%ar)'`), plus branches updated in the window and the current branch's ahead/behind status.
- **PRs & CI:** open PRs (title, author, review state, mergeable), and the CI/check status on each PR head and the default branch. Highlight anything red or conflicted.
- **Issues:** issues opened, updated, or assigned in the window; note anything labeled bug/urgent.
- **Deploy/prod health:** if Railway or Supabase tools are available, check latest deployment status, recent errors in logs, and advisor warnings. Skip quietly if unavailable.

## 3. Output format
1. **Headline** - one sentence on overall state (green / needs attention).
2. **Needs attention first** - failing CI, conflicts, failed deploys, urgent issues, PRs waiting on review.
3. **What changed** - bullets grouped by branch/PR, with author and short summary.
4. **Open items** - PRs and issues still pending.
5. **Suggested next step** - one or two concrete actions.

Read-only: do not push, merge, comment, or change anything.
