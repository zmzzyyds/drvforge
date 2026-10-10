# drvforge

**Scaffolding tool for modern Linux kernel driver projects.**

[![CI](https://github.com/zmzzyyds/drvforge/actions/workflows/ci.yml/badge.svg)](https://github.com/zmzzyyds/drvforge/actions/workflows/ci.yml)
[![License: GPL v2](https://img.shields.io/badge/License-GPL%20v2-blue.svg)](https://www.gnu.org/licenses/old-licenses/gpl-2.0.html)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)

`drvforge` generates a complete, buildable out-of-tree Linux driver project
with one command: the driver source (modern kernel style), Makefile,
Kconfig, DKMS config, Device Tree overlay and a userspace C test client.
Every generated driver is compiled against a real kernel in CI, so templates
stay valid as the kernel evolves.

> **English** | [简体中文](README.zh-CN.md)

## Why

Bringing up a first kernel driver means copying boilerplate from five
different tutorials of five different ages, guessing which API is current,
hand-writing DKMS and overlay files, and only discovering mistakes at the
first `insmod`. drvforge gives you one consistent, current starting point —
and a reference for how each subsystem (misc, cdev, IIO, …) is wired
together today.

## Templates

| Template | What it generates |
| --- | --- |
| `misc` | Platform driver + `misc` char device, in-memory echo buffer, sysfs attribute — no hardware needed |
| `platform-cdev` | Platform driver with a full `cdev`, a shared UAPI ioctl header, validated ioctls, userspace client |
| `iio-temp` | I2C temperature sensor using `regmap` + the IIO subsystem (`in_temp_raw`/`in_temp_scale`) |

More subsystems are tracked in [the roadmap](#roadmap) and CONTRIBUTING.md;
adding a template is designed to be a good first kernel-tooling PR.

## Install

```sh
# recommended: isolated install with pipx
pipx install git+https://github.com/zmzzyyds/drvforge.git

# or with pip
pip install git+https://github.com/zmzzyyds/drvforge.git

# or from a checkout, for development
git clone https://github.com/zmzzyyds/drvforge.git
cd drvforge
pip install -e ".[dev]"
```

## Quick start

```sh
# 1. check the kernel toolchain (headers, gcc, dtc, dkms, qemu)
drvforge env-check

# 2. list templates
drvforge list

# 3. generate a project
drvforge new my-sensor -t misc -c acme,my-sensor
#   -> ./my_sensor/

# 4. build and test on a Linux host
cd my_sensor
make            # builds my_sensor.ko against your running kernel
make test       # builds, loads, runs the userspace test, unloads
```

Generated layout:

```
my_sensor/
├── my_sensor.c            # driver source
├── Makefile               # out-of-tree build + load/test/DKMS targets
├── Kconfig                # ready to move into the kernel tree
├── dkms.conf              # DKMS packaging
├── my_sensor-overlay.dts  # Device Tree overlay (QEMU virt example)
├── tools/
│   └── test.c             # userspace C test client
└── README.md              # build, bind, test, upstream instructions
```

The `platform-cdev` template additionally emits `include/my_sensor.h`, a
shared UAPI header included by both the driver and the userspace client.

## Requirements

- **drvforge itself:** Python 3.9+, runs on Linux/macOS/Windows.
- **Building generated modules:** a Linux host (or VM/container) with
  `build-essential` and `linux-headers-$(uname -r)`.
- Templates use current kernel APIs (e.g. `remove_new`, `dev_err_probe`,
  the single-argument I2C `probe`, `devm_iio_device_register`); kernel
  **6.3+** is recommended (the misc/cdev templates compile on 5.19+). CI
  builds against the Ubuntu 24.04 kernel.

## Project status

v0.1.0 — three templates, stable CLI, CI compiling every generated driver.
The tooling is usable for real work; expect template coverage to grow.

## Roadmap

- [ ] More driver templates: `hwmon`, `leds`, `input`, `pwm`, `rtc`,
      `watchdog`, `net`, USB, DRM mini-driver
- [ ] `drvforge check` — run `checkpatch.pl` and sparse on the generated code
- [ ] `scripts/qemu-try.sh` — one-command QEMU arm64 boot + overlay + test
- [ ] YAML devicetree binding generation alongside overlays
- [ ] Kernel-version compatibility matrix in CI (multiple LTS kernels)
- [ ] Interactive mode (`drvforge new` prompting for resources, IRQs,
      sysfs attributes)

## Contributing

Bug reports, template requests and PRs are welcome. Please read
[CONTRIBUTING.md](CONTRIBUTING.md) and
[docs/writing-templates.md](docs/writing-templates.md) before adding a
template. By participating you agree to the code of conduct.

## License

GPL-2.0-only, consistent with the Linux kernel — driver templates are
derivative works of the kernel. See [LICENSE](LICENSE).
