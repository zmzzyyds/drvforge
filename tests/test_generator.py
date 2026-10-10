"""Tests for template validation and rendering."""

import pytest

from drvforge.generator import (
    TEMPLATES,
    GenerationError,
    ProjectConfig,
    generate,
    normalize_module_name,
    parse_compatible,
)

COMPATS = {
    "misc": "acme,demo-misc",
    "platform-cdev": "acme,demo-cdev",
    "iio-temp": "acme,demo-temp",
}


@pytest.mark.parametrize("key", sorted(TEMPLATES))
def test_every_template_renders_completely(key, tmp_path):
    config = ProjectConfig(
        raw_name="my-widget",
        template_key=key,
        compatible=COMPATS[key],
        author="Tester",
        email="tester@example.com",
    )
    out_dir = tmp_path / config.module_name

    written = generate(config, out_dir)

    spec = TEMPLATES[key]
    assert len(written) == len(spec.files)

    for path in written:
        assert path.is_file()
        assert path.stat().st_size > 0
        text = path.read_text(encoding="utf-8")
        # No unresolved Jinja expressions may survive rendering.
        assert "{{" not in text, f"unrendered Jinja in {path}"
        assert "{%" not in text, f"unrendered Jinja tag in {path}"

    driver = (out_dir / "my_widget.c").read_text(encoding="utf-8")
    assert 'MODULE_LICENSE("GPL v2")' in driver
    assert COMPATS[key] in driver
    assert "my_widget" in driver

    assert (out_dir / "Makefile").is_file()
    assert (out_dir / "Kconfig").is_file()
    assert (out_dir / "dkms.conf").is_file()
    assert (out_dir / "my_widget-overlay.dts").is_file()
    assert (out_dir / "tools" / "test.c").is_file()
    assert (out_dir / "README.md").is_file()


def test_platform_cdev_emits_uapi_header(tmp_path):
    config = ProjectConfig(
        raw_name="gain-dev",
        template_key="platform-cdev",
        compatible="acme,gain-dev",
        author="Tester",
        email="tester@example.com",
    )
    out_dir = tmp_path / config.module_name
    generate(config, out_dir)

    header = out_dir / "include" / "gain_dev.h"
    assert header.is_file()
    text = header.read_text(encoding="utf-8")
    assert "GAIN_DEV_IOC_MAGIC" in text
    assert "_IOR" in text and "_IOW" in text


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("my-sensor", "my_sensor"),
        ("My.Sensor!", "my_sensor"),
        ("tmp100", "tmp100"),
        ("  Foo Bar  ", "foo_bar"),
    ],
)
def test_normalize_module_name(raw, expected):
    assert normalize_module_name(raw) == expected


@pytest.mark.parametrize("raw", ["42sensor", "---", "   "])
def test_invalid_module_names(raw):
    with pytest.raises(GenerationError):
        normalize_module_name(raw)


@pytest.mark.parametrize("compat", ["acme,tmp100", "vendor-1,board_2"])
def test_valid_compatible(compat):
    vendor, board = parse_compatible(compat)
    assert vendor and board


@pytest.mark.parametrize("compat", ["ACME,x", "no-comma", "a,", ",b", "a,Bad"])
def test_invalid_compatible(compat):
    with pytest.raises(GenerationError):
        parse_compatible(compat)


def test_compat_required_for_templates(tmp_path):
    with pytest.raises(GenerationError):
        ProjectConfig(raw_name="x", template_key="misc")


def test_unknown_template_rejected():
    with pytest.raises(GenerationError):
        ProjectConfig(raw_name="x", template_key="does-not-exist",
                      compatible="a,b")


def test_existing_files_are_not_overwritten(tmp_path):
    config = ProjectConfig(
        raw_name="dev",
        template_key="misc",
        compatible="acme,dev",
        author="T",
        email="t@example.com",
    )
    generate(config, tmp_path)
    with pytest.raises(GenerationError):
        generate(config, tmp_path, force=False)
    # force=True succeeds
    generate(config, tmp_path, force=True)
