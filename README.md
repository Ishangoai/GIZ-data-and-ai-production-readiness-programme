# Data and AI Production Readiness Programme

Welcome to the Ishango Data and AI Production Readiness Programme, delivered for the GIZ cohort.

This programme develops practical skills in building, testing and deploying data and AI applications. Topics include APIs, Docker, software engineering practices, CI/CD, data engineering, MLOps and AI agents.

## Teaching team

- **Lead facilitator:** Shadrack Darku
- **Supporting facilitators:** Solomon Eshun and Vincent Aduuna Frimpong
- **Additional support:** Ishango data scientists and cofounders

## Course format

- Live sessions every Tuesday, 11:00–13:00 GMT.
- Fifteen lecture decks grouped across ten meetings.
- Three practical labs.
- Questions, announcements and support through the course Slack channel.

Use the lecture slides and lab briefs shared by the teaching team alongside this repository.

## Getting started

1. Accept your invitation to collaborate on this repository.
2. Sign in using the GitHub account registered for the programme.
3. Select the `development` branch.
4. Create a feature branch using this naming convention: `feature-branch-YOUR-GITHUB-USERNAME`.
5. Open your feature branch in GitHub Codespaces using the smallest available machine size supported by the repository.
6. Allow the development environment setup to finish before running code.
7. Follow the onboarding instructions for creating your student folder and testing your application.

If you already have a feature branch, continue working on that branch rather than creating a duplicate.

## Working in the terminal

Activate the project's Python environment:

```bash
source .venv/bin/activate
```

Deactivate it when needed:

```bash
deactivate
```

Check the active Python interpreter:

```bash
which python
```

List installed Python packages:

```bash
uv pip list
```

Find the Python interpreter selected by uv:

```bash
uv python find
```

## Checking your code

Run unit tests:

```bash
uv run pytest
```

Run Ruff lint checks:

```bash
uv run ruff check
```

Run type checks:

```bash
uv run pyright
```

Run these commands from the repository root. Refer to `pyproject.toml` for project dependencies and available commands.

## Submitting your work

1. Save and test your changes.
2. Check that your changes belong to your assigned student folder.
3. Commit and push your feature branch.
4. Open a pull request with `development` as the base branch.
5. Review the automated checks and resolve any failures.
6. Request review from the teaching team and follow their merge instructions.

Do not push directly to `development` or `main`.

## Checking your deployment

After your pull request is merged, check the repository's **Actions** tab for the deployment result.

When deployment succeeds, use the service URL shown in the logs to test your application. Follow the onboarding guide for the required endpoint checks.

A successful local test and a successful cloud deployment are separate checks.

## Codespaces usage

Stop your Codespace when you finish working to conserve compute usage.

If you reach your usage allowance, contact the teaching team. Do not delete a Codespace containing work you have not pushed to GitHub.

## Getting help

Ask in the course Slack channel and include:

- Your GitHub username.
- The step you were following.
- The command and exact error message.
- Your branch, pull request or failed workflow link, where relevant.

Never share API keys, passwords or access tokens in messages, screenshots or commits.
