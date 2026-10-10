"""Template registry and rendering engine for drvforge.

Each driver template lives in ``src/drvforge/templates/<key>/`` and consists
of a fixed set of files. File names may themselves contain Jinja expressions
(e.g. ``{{ module_name }}.c``) so that the generated project uses the name the
caller requested.
"""

from __future__ import annotations

import datetime
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

TEMPLATE_ROOT = Path(__file__).parent / "templates"

# Mapping of template source files (relative to the template directory) to
# rendered destination paths (Jinja-rendered, relative to the output project).
_COMMON_FILES: list[tuple[str, str]] = [
    ("driver.c.jinja", "{{ module_name }}.c"),
    ("Makefile.jinja", "Makefile"),
    ("Kconfig.jinja", "Kconfig"),
    ("dkms.conf.jinja", "dkms.conf"),
    ("overlay.dts.jinja", "{{ module_name }}-overlay.dts"),
    ("test.c.jinja", "tools/test.c"),
    ("README.md.jinja", "README.md"),
]


_CDEV_FILES: list[tuple[str, str]] = [
    ("driver.c.jinja", "{{ module_name }}.c"),
    ("uapi.h.jinja", "include/{{ module_name }}.h"),
    ("Makefile.jinja", "Makefile"),
    ("Kconfig.jinja", "Kconfig"),
    ("dkms.conf.jinja", "dkms.conf"),
    ("overlay.dts.jinja", "{{ module_name }}-overlay.dts"),
    ("test.c.jinja", "tools/test.c"),
    ("README.md.jinja", "README.md"),
]


@dataclass(frozen=True)
class TemplateSpec:
    """Metadata describing a driver template."""

    key: str
    label: str
    description: str
    files: list[tuple[str, str]]
    needs_compat: bool = True


TEMPLATES: dict[str, TemplateSpec] = {
    "misc": TemplateSpec(
        key="misc",
        label="misc platform device",
        description=(
            "A platform driver that registers a misc character device with an "
            "in-memory echo buffer and a sysfs attribute. No real hardware "
            "required: ideal first out-of-tree driver."
        ),
        files=_COMMON_FILES,
    ),
    "platform-cdev": TemplateSpec(
        key="platform-cdev",
        label="platform device with cdev + ioctl",
        description=(
            "A platform driver implementing a full character device "
            "(cdev_region, file_operations, ioctl) with a userspace C test "
            "client. Covers the classic userspace/kernel API contract."
        ),
        files=_CDEV_FILES,
    ),
    "iio-temp": TemplateSpec(
        key="iio-temp",
        label="I2C IIO temperature sensor",
        description=(
            "An I2C temperature sensor driver using regmap and the IIO "
            "subsystem (read_raw, info mask, scale/offset). Reference style "
            "for bringing up a new IIO sensor."
        ),
        files=_COMMON_FILES,
    ),
}


class GenerationError(Exception):
    """Raised when a project cannot be generated."""


def normalize_module_name(name: str) -> str:
    """Convert an arbitrary project name into a valid C identifier / module name.

    Kernel C identifiers and module names must use ``[a-z0-9_]`` and may not
    start with a digit.
    """

    module = re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")
    if not module:
        raise GenerationError(
            f"Project name {name!r} contains no usable characters; "
            "use letters and digits, e.g. 'my-sensor'."
        )
    if module[0].isdigit():
        raise GenerationError(
            f"Module name {module!r} must not start with a digit "
            "(C identifier requirement)."
        )
    return module


def parse_compatible(compat: str) -> tuple[str, str]:
    """Validate and split a Device Tree ``compatible`` string.

    Accepts the canonical ``vendor,board`` form with lowercase letters, digits,
    dashes and underscores.
    """

    compat = compat.strip()
    match = re.fullmatch(r"[a-z0-9][a-z0-9_-]*,[a-z0-9][a-z0-9_-]*", compat)
    if not match:
        raise GenerationError(
            f"Invalid compatible string {compat!r}; expected 'vendor,board', "
            "e.g. 'acme,tmp100' (lowercase letters, digits, '-' or '_')."
        )
    vendor, board = compat.split(",", 1)
    return vendor, board


def git_identity() -> tuple[str, str]:
    """Best-effort lookup of the user's git name/email for file headers."""

    def _cfg(key: str) -> str:
        try:
            out = subprocess.run(
                ["git", "config", "--get", key],
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
            return out.stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return ""

    name = _cfg("user.name") or "Your Name"
    email = _cfg("user.email") or "you@example.com"
    return name, email


@dataclass
class ProjectConfig:
    """Validated configuration for one generated driver project."""

    raw_name: str
    template_key: str
    compatible: str | None = None
    author: str | None = None
    email: str | None = None

    module_name: str = ""
    driver_name: str = ""
    name_upper: str = ""
    compat_vendor: str = ""
    compat_board: str = ""

    def __post_init__(self) -> None:
        spec = TEMPLATES.get(self.template_key)
        if spec is None:
            raise GenerationError(
                f"Unknown template {self.template_key!r}. "
                f"Available: {', '.join(sorted(TEMPLATES))}."
            )
        self.module_name = normalize_module_name(self.raw_name)
        self.driver_name = self.module_name.replace("_", "-")
        self.name_upper = re.sub(r"[^A-Z0-9]", "_", self.module_name.upper())
        if spec.needs_compat:
            if not self.compatible:
                raise GenerationError(
                    f"Template {self.template_key!r} requires --compat 'vendor,board'."
                )
            self.compat_vendor, self.compat_board = parse_compatible(self.compatible)
        if not self.author or not self.email:
            git_name, git_email = git_identity()
            self.author = self.author or git_name
            self.email = self.email or git_email

    @property
    def context(self) -> dict[str, object]:
        """Jinja rendering context."""

        return {
            "project_name": self.raw_name,
            "module_name": self.module_name,
            "driver_name": self.driver_name,
            "name_upper": self.name_upper,
            "compat": self.compatible,
            "compat_vendor": self.compat_vendor,
            "compat_board": self.compat_board,
            "author": self.author,
            "email": self.email,
            "license": "GPL v2",
            "year": datetime.date.today().year,
        }


def _make_environment(template_dir: Path) -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
        trim_blocks=False,
        lstrip_blocks=False,
    )
    env.globals["min"] = min
    env.globals["max"] = max
    return env


def generate(config: ProjectConfig, out_dir: Path, force: bool = False) -> list[Path]:
    """Render every file of the selected template into ``out_dir``.

    Returns the sorted list of written paths. Raises ``GenerationError`` if a
    destination already exists and ``force`` is False.
    """

    spec = TEMPLATES[config.template_key]
    template_dir = TEMPLATE_ROOT / spec.key
    if not template_dir.is_dir():
        raise GenerationError(f"Template directory missing: {template_dir}")

    env = _make_environment(template_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    for source_name, dest_pattern in spec.files:
        source_path = template_dir / source_name
        if not source_path.is_file():
            raise GenerationError(f"Template file missing: {source_path}")
        rel_dest = env.from_string(dest_pattern).render(**config.context)
        dest = out_dir / rel_dest
        if dest.exists() and not force:
            raise GenerationError(
                f"Refusing to overwrite existing file: {dest}. "
                "Re-run with --force to overwrite."
            )
        dest.parent.mkdir(parents=True, exist_ok=True)
        rendered = env.get_template(source_name).render(**config.context)
        dest.write_text(rendered, encoding="utf-8", newline="\n")
        written.append(dest)

    # Rendered shell helpers need the executable bit on POSIX systems.
    return sorted(written)


def available_templates() -> list[TemplateSpec]:
    return [TEMPLATES[key] for key in sorted(TEMPLATES)]


def check_toolchain() -> dict[str, str | None]:
    """Return a mapping of tool name -> resolved path (None when missing)."""

    tools = ["make", "gcc", "clang", "dtc", "dkms", "qemu-system-aarch64"]
    return {tool: shutil.which(tool) for tool in tools}
