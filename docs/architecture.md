# Architecture

drvforge is intentionally small: a template registry, a rendering engine and
a thin CLI.

## Components

```
src/drvforge/
├── cli.py          # argparse commands: new / list / env-check
├── generator.py    # ProjectConfig validation, TemplateSpec registry, renderer
└── templates/
    ├── misc/
    ├── platform-cdev/
    └── iio-temp/
```

### `TemplateSpec`

Each template is described by a frozen `TemplateSpec`:

- `key` — CLI identifier (`--type`)
- `label` / `description` — shown by `drvforge list`
- `files` — list of `(template_source, rendered_destination)` pairs; both
  sides are Jinja-rendered, so destinations can contain `{{ module_name }}`
- `needs_compat` — whether a Device Tree `compatible` string is required

### `ProjectConfig`

Validates and normalises user input before rendering:

- project name → `module_name` (`[a-z0-9_]+`, no leading digit),
  `driver_name` (hyphenated) and `name_upper`
- `--compat` is validated as `vendor,board` and split into
  `compat_vendor` / `compat_board`
- author/email default to `git config user.name` / `user.email`
- `year` is provided for copyright headers

Validation failures raise `GenerationError`; the CLI maps those to exit code
2 with a readable message.

### Rendering

- Jinja2 with `StrictUndefined` — a missing variable is an error, never a
  blank string.
- `keep_trailing_newline=True` and explicit `newline="\n"` on write, so
  generated files are byte-stable across platforms (important for
  checkpatch and diffs).
- Existing files are never overwritten without `--force`.

## Template variables

| Variable | Example |
| --- | --- |
| `project_name` | `my-sensor` (raw input) |
| `module_name` | `my_sensor` |
| `driver_name` | `my-sensor` |
| `name_upper` | `MY_SENSOR` |
| `compat` | `acme,my-sensor` |
| `compat_vendor` / `compat_board` | `acme` / `my-sensor` |
| `author` / `email` / `year` | from flags or git config |

## Testing strategy

1. **Unit/integration tests** (`tests/`): every template is rendered and
   checked for unresolved Jinja, required kernel macros, the compatible
   string and the full expected file set.
2. **Real kernel build** (CI `build-modules` job): generate all templates on
   Ubuntu, `make` each module against `linux-headers-$(uname -r)`, compile
   the userspace clients, and smoke-load every `.ko` with `insmod`/`rmmod`.
3. **Device tree**: path-based platform overlays are compiled with `dtc` in
   CI; label-based I2C overlays require a board DTB and are checked
   manually.

The golden rule: **a template that does not compile in CI does not merge.**

## Design constraints

- Generated code is GPL-2.0-only and must follow kernel coding style.
- Templates target current mainline APIs; incompatible API changes get
  `LINUX_VERSION_CODE` guards, not unconditional new calls.
- The generator stays dependency-light (Jinja2 only) and runs on any OS;
- kernel-specific operations belong to generated Makefiles and docs, not to
  the Python tool.
