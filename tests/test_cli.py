"""End-to-end tests for the drvforge CLI."""

from drvforge.cli import main


def test_list_templates(capsys):
    assert main(["list"]) == 0
    out = capsys.readouterr().out
    assert "misc" in out
    assert "platform-cdev" in out
    assert "iio-temp" in out


def test_new_creates_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    rc = main(["new", "my-sensor", "-t", "misc", "-c", "acme,my-sensor"])
    assert rc == 0
    assert (tmp_path / "my_sensor" / "my_sensor.c").is_file()
    assert (tmp_path / "my_sensor" / "tools" / "test.c").is_file()


def test_new_refuses_then_force_overwrites(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    args = ["new", "s", "-t", "misc", "-c", "acme,s"]
    assert main(args) == 0
    assert main(args) == 2  # refuses to overwrite
    assert main(args + ["--force"]) == 0


def test_bad_name_exits_nonzero(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    rc = main(["new", "9bad", "-t", "misc", "-c", "a,b"])
    assert rc == 2


def test_missing_compat_exits_nonzero(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    rc = main(["new", "s", "-t", "iio-temp"])
    assert rc == 2


def test_env_check_runs():
    # Returns 0 on a fully equipped Linux host, 1 otherwise; it must never raise.
    assert main(["env-check"]) in (0, 1)


def test_version(capsys):
    try:
        main(["--version"])
    except SystemExit as exc:
        assert exc.code == 0
    assert "drvforge" in capsys.readouterr().out
