# Writing a new driver template

New templates are the main way to contribute to drvforge. A template is a
directory under `src/drvforge/templates/<key>/` plus a `TemplateSpec` entry.

## 1. Pick the scope

A good template covers **one** standard driver pattern for one subsystem:

- one bus/attachment (platform, I2C, SPI, USB, PCI)
- one userspace-facing interface (misc, cdev, sysfs, IIO, hwmon, input, …)
- no real hardware required to smoke-test whenever possible

Browse the in-tree drivers for the canonical pattern; templates should mimic
a well-reviewed mainline driver, not invent a new style.

## 2. Create the template directory

The common file set:

```
templates/<key>/
├── driver.c.jinja      # {{ module_name }}.c
├── Makefile.jinja      # out-of-tree build + load/test/DKMS targets
├── kconfig.jinja       # Kconfig fragment
├── dkms.conf.jinja
├── overlay.dts.jinja   # {{ module_name }}-overlay.dts
├── test.c.jinja       # tools/test.c userspace client
└── README.md.jinja     # generated project README
```

Add extra files when the pattern genuinely needs them (for example
`platform-cdev` emits a shared `include/{{ module_name }}.h` UAPI header).

## 3. Register the template

In `src/drvforge/generator.py`:

1. Define a file list (reuse `_COMMON_FILES` or add a new one).
2. Add a `TemplateSpec` to `TEMPLATES` with a one-sentence label and a
   description that explains when a user should pick it.

## 4. Template variables

See [architecture.md](architecture.md) for the full list. Use
`{{ module_name }}` for C identifiers and file names, `{{ name_upper }}` for
macro prefixes and `{{ compat }}` for the of_match table.

## 5. Kernel code requirements

- SPDX header first, then a file comment explaining what the driver does.
- Modern APIs: `devm_*`, `dev_err_probe()`, `remove_new`,
  `module_*_driver()` helpers.
- Every userspace boundary validated: `copy_{to,from}_user` checks, ioctl
  magic/`_IOC_DIR` checks, bounded sysfs writes.
- Guard incompatible API changes with `LINUX_VERSION_CODE` and state the
  minimum kernel in the generated README.
- Run `scripts/checkpatch.pl --strict -f <file>` on the rendered output.

## 6. Userspace test client

`tools/test.c` must:

- compile with `-Wall -Wextra -Werror`-clean style;
- exit `0` on success and non-zero on failure;
- print `[ok]` / `PASS:` lines so CI logs are readable;
- need no arguments (fixed device paths / IIO name lookup).

## 7. Tests

Add cases to `tests/test_generator.py`:

- the template is already covered by the parametrised render test;
- add assertions for anything unique (extra files, special strings);
- add a CLI test if behaviour differs.

## 8. Documentation

- Generated `README.md.jinja`: requirements, build/test, how the device is
  instantiated (overlay / sysfs `new_device` / QEMU), how to adapt to real
  silicon, how to move the code into the kernel tree.
- Add the template to the tables in both `README.md` and
  `README.zh-CN.md`, and a CHANGELOG entry.

## 9. Before opening the PR

- [ ] `pytest` and `ruff check src tests` pass
- [ ] generated module builds on a current kernel (CI runs on Ubuntu 24.04)
- [ ] `make test` works, or the limitation is documented
- [ ] checkpatch is clean

If your template needs hardware that CI cannot provide, that is fine — the
build job still compiles it; say in the PR how you verified runtime
behaviour.
