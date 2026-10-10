"""Command line interface for drvforge."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .generator import (
    TEMPLATES,
    GenerationError,
    ProjectConfig,
    available_templates,
    check_toolchain,
    generate,
)


def _add_new_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "new",
        help="generate a new driver project",
        description="Generate a complete out-of-tree kernel driver project.",
    )
    parser.add_argument("name", help="project / driver name, e.g. 'my-sensor'")
    parser.add_argument(
        "-t",
        "--type",
        required=True,
        choices=sorted(TEMPLATES),
        help="driver template to use",
    )
    parser.add_argument(
        "-c",
        "--compat",
        help="Device Tree compatible string, e.g. 'acme,tmp100'",
    )
    parser.add_argument("--author", help="author name for file headers (defaults to git config)")
    parser.add_argument("--email", help="author email for file headers (defaults to git config)")
    parser.add_argument(
        "-d",
        "--dir",
        default=".",
        help="output directory (default: current directory)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite existing files instead of aborting",
    )
    parser.set_defaults(func=_cmd_new)


def _cmd_new(args: argparse.Namespace) -> int:
    try:
        config = ProjectConfig(
            raw_name=args.name,
            template_key=args.type,
            compatible=args.compat,
            author=args.author,
            email=args.email,
        )
        out_dir = Path(args.dir) / config.module_name
        written = generate(config, out_dir, force=args.force)
    except GenerationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    spec = TEMPLATES[args.type]
    print(f"Generated {len(written)} files for '{config.module_name}' "
          f"({spec.label}) in {out_dir}")
    for path in written:
        try:
            rel = path.relative_to(Path.cwd())
        except ValueError:
            rel = path
        print(f"  + {rel}")
    print()
    print("Next steps:")
    print(f"  cd {out_dir}")
    print("  make            # build the module (needs kernel headers)")
    print("  sudo make load  # load via insmod")
    print("  make test       # build & run the userspace test client")
    return 0


def _cmd_list(_args: argparse.Namespace) -> int:
    print("Available driver templates:\n")
    for spec in available_templates():
        print(f"  {spec.key:<14} {spec.label}")
        print(f"  {' ' * 14} {spec.description}\n")
    return 0


def _cmd_env_check(_args: argparse.Namespace) -> int:
    print("Kernel development toolchain check:\n")
    found = True
    for tool, path in check_toolchain().items():
        status = path if path else "NOT FOUND"
        if path is None:
            found = False
        print(f"  {tool:<22} {status}")
    print()
    if found:
        print("All tools available. You can build generated modules locally.")
        return 0
    print("Some tools are missing.")
    print("  Debian/Ubuntu: sudo apt install build-essential linux-headers-$(uname -r) "
          "device-tree-compiler dkms qemu-system-arm")
    print("  Fedora:        sudo dnf install kernel-devel dtc dkms qemu-system-aarch64-gnu")
    print()
    print("Note: drvforge itself runs anywhere Python runs; kernel modules can only be "
          "built on a Linux host (or a Linux VM/container).")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="drvforge",
        description="Scaffold modern Linux kernel driver projects.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  drvforge list\n"
            "  drvforge new my-sensor -t misc -c acme,my-sensor\n"
            "  drvforge new tmp100 -t iio-temp -c ti,tmp100 -d ~/work\n"
        ),
    )
    parser.add_argument("--version", action="version", version=f"drvforge {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)
    _add_new_parser(subparsers)

    list_parser = subparsers.add_parser("list", help="list available driver templates")
    list_parser.set_defaults(func=_cmd_list)

    env_parser = subparsers.add_parser("env-check", help="check local kernel build toolchain")
    env_parser.set_defaults(func=_cmd_env_check)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)
