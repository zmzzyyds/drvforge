# Changelog

All notable changes to drvforge are documented in this file. The format is
based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the
project follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- `hwmon`, `leds`, `input`, `pwm`, `rtc`, `watchdog` templates (planned)
- `drvforge check` running checkpatch.pl/sparse (planned)
- One-command QEMU arm64 try-out script (planned)

### Fixed
- The `misc` and `platform-cdev` overlays could not be applied to the QEMU
  arm64 `virt` machine they claimed to target: they attached to `&{/soc}`,
  which the virt machine does not have, and their `reg` carried one cell too
  many for the root bus (`#address-cells = 2`, `#size-cells = 1`). Both now
  attach to `&{/}`, declare the cell counts, and merge cleanly.
- Generated READMEs no longer present the configfs overlay route as the only
  way to bind at runtime — `CONFIG_OF_CONFIGFS` is not in mainline. The QEMU
  path now shows the `-M virt,dumpdtb=` step needed to obtain the tree to
  merge into, and notes that it must be dumped with the same `-cpu`/`-m`/`-smp`
  used to boot.

## [0.1.0] - 2026-10-10

### Added
- `drvforge new` project generator with Jinja2 templates
- `misc` template: platform driver + misc char device + sysfs attribute
- `platform-cdev` template: full cdev with shared UAPI ioctl header and
  validated ioctl commands
- `iio-temp` template: I2C temperature sensor using regmap + IIO
- Every generated project includes Makefile, Kconfig, dkms.conf, Device Tree
  overlay, userspace C test client and README
- `drvforge list` and `drvforge env-check` commands
- CI: pytest + ruff, plus a real-kernel build and smoke-load job for every
  generated driver

[Unreleased]: https://github.com/zmzzyyds/drvforge/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/zmzzyyds/drvforge/releases/tag/v0.1.0
