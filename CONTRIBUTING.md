# Contributing to drvforge

Thanks for your interest in improving drvforge! This project is young, and
good templates are the most valuable contribution.

## Getting started

```sh
git clone https://github.com/__GH_USER__/drvforge.git
cd drvforge
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest          # render every template and run CLI tests
ruff check src tests
```

## Ways to contribute

- **New driver templates** — see [docs/writing-templates.md](docs/writing-templates.md).
  Open an issue first to discuss scope and naming; `hwmon`, `leds`, `input`,
  `pwm`, `rtc` and `watchdog` templates are high priority.
- **Template correctness** — fixes for newer/older kernel API changes,
  missing error handling, better comments, or checkpatch complaints.
- **The generator/CLI** — bug fixes and the roadmap features in README.md.
- **Docs** — corrections, translations, kernel bring-up notes for new boards.

## Pull request checklist

- [ ] `pytest` passes locally and in CI.
- [ ] `ruff check src tests` is clean.
- [ ] New templates render with **no unresolved Jinja** and include the full
      common file set (driver, Makefile, Kconfig, dkms.conf, overlay,
      userspace test, generated README).
- [ ] Generated driver code builds against a current kernel; if you cannot
      run a Linux build locally, say so in the PR and a maintainer will run
      the CI build job on your branch.
- [ ] Generated C follows kernel style (`scripts/checkpatch.pl --strict`
      should be clean apart from accepted false positives).
- [ ] Commit messages explain the *why*, not just the *what*.
- [ ] User-facing changes get a CHANGELOG.md entry under "Unreleased".

## Commit messages

Use imperative mood ("add hwmon template", "fix class_create on 6.4+").
One logical change per commit.

## Kernel compatibility policy

Templates target current mainline APIs and the latest two LTS kernels. When
an API changed incompatibly, prefer a `LINUX_VERSION_CODE` guard (see the
`class_create` handling in the platform-cdev template) and note the oldest
supported kernel in the generated README.

## Code of conduct

Participation is governed by [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
Please be kind and technical.
