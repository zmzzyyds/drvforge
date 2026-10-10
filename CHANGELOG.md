# Changelog

All notable changes to drvforge are documented in this file. The format is
based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the
project follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- `hwmon`, `leds`, `input`, `pwm`, `rtc`, `watchdog` templates (planned)
- `drvforge check` running checkpatch.pl/sparse (planned)
- One-command QEMU arm64 try-out script (planned)

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
