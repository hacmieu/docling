# Plan Entry - Next Steps After Fork

## Immediate next steps

1. Sync local `main` from upstream:
   - `git checkout main`
   - `git fetch upstream`
   - `git rebase upstream/main`
2. Push synced `main` to your fork:
   - `git push origin main`
3. Start feature work in dedicated branch:
   - `git checkout -b feat/<topic>`
   - code, test, commit
   - `git push -u origin feat/<topic>`
4. Open PR from `hacmieu:feat/<topic>` to `docling-project:main`.
