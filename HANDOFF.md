# Picking up SomniAI development

For the person taking over development. Follow these in order; it takes about an
hour, most of it installs.

## 1. What you need from the project owners first

You cannot start without these. They must be sent **privately** (a direct message,
not email lists, never committed to the repo):

| Item | Why |
| --- | --- |
| Collaborator access to the GitHub repository | to push the `develop` branch |
| Values for `.env.local` | the app needs a database and an auth secret to run |
| The file `.anonymity-terms.local` | powers the guard that keeps author names out of the public repo |

Ask for **your own MongoDB Atlas database user**, not a shared password.

## 2. Install

| Tool | Version | Check |
| --- | --- | --- |
| Git | any recent | `git --version` |
| Node.js | 20 LTS or newer | `node --version` |
| Python | 3.11–3.13 | `python --version` |
| Claude Code | latest | `claude --version` |

Android Studio and a JDK are only needed from Phase 2. Prompt 2.1 will tell you
exactly what to install then.

## 3. Get the code

**On Windows, use a short path.** A long path breaks the Python install in a
misleading way (`No module named 'numpy._utils'`).

```bash
git clone https://github.com/<owner>/SomniAI--Smart-Automated-Alarm.git C:/somniai
cd C:/somniai
git checkout research/evaluation-pipeline
```

Use the repository URL the owners give you. Start from that branch; prompt 0.1
creates `develop` from it, and all your work goes on `develop`.

## 4. Put the private files in place

- Copy `.env.local.example` to `.env.local` and fill in the values you were sent.
  Generate your own `NEXTAUTH_SECRET` if you weren't given one:
  `node -e "console.log(require('crypto').randomBytes(32).toString('base64'))"`
- Save `.anonymity-terms.local` in the repository root.

Both are gitignored. Confirm with `git status`: neither should appear.

## 5. Install dependencies

```bash
npm install
cd ai-brain
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements-lock.txt
cd ..
```

## 6. Confirm you match the baseline

```bash
npm test                                   # expect 70 passed
npx tsc --noEmit                           # expect no output
cd ai-brain && python -m pytest -p no:warnings && cd ..   # expect 283 passed, 28 skipped
node scripts/check-anonymity.mjs           # expect "clean"
```

`next build` is **expected to fail** right now. That is prompt 0.1's job, not a
problem with your setup. If anything else differs from the numbers above, stop
and sort it out before starting: the plan relies on knowing the starting point.

## 7. Start

```bash
claude
```

Claude Code reads `CLAUDE.md` automatically. Your first message:

> Read CLAUDE.md and DEVELOPMENT_PLAN.md, confirm you understand the hard rules
> and the current progress, then tell me what prompt 0.1 will change before
> starting it.

Then paste prompt **0.1** from `DEVELOPMENT_PLAN.md`, and continue one prompt at a
time. After each one, check that the gate passed and that `CLAUDE.md`'s
**Progress** table was updated.

## Rules that matter most

1. **Never put a name, email, institution or GitHub username in any file in the
   repo.** The paper is under anonymous review and the repo is public. Run
   `node scripts/check-anonymity.mjs` before every push.
2. **Never commit to, delete or force-push `research/evaluation-pipeline`, and
   never make the repo private.** The paper's review artifact depends on it.
3. **Red is not done.** Don't move to the next prompt with a failing check.

## When you get a phone involved

From Phase 2 you need an Android phone with USB debugging enabled. If you can
borrow a cheap Xiaomi, Realme or Oppo as well, do: those are the phones where
alarms fail in practice, and prompts 2.7 and 3.1 are written for them.
