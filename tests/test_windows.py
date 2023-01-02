from opensafely import windows


def test_ensure_tty_not_windows(monkeypatch):
    monkeypatch.setattr(windows.sys, "platform", "linux")
    assert windows.ensure_tty(["cmd"]) == ["cmd"]


def test_ensure_tty_no_winpty(monkeypatch):
    monkeypatch.setattr(windows.sys, "platform", "win32")
    monkeypatch.setattr(windows.shutil, "which", lambda x: None)
    assert windows.ensure_tty(["cmd"]) == ["cmd"]


def test_ensure_tty_isatty(monkeypatch):
    monkeypatch.setattr(windows.sys, "platform", "win32")
    monkeypatch.setattr(windows.shutil, "which", lambda x: "/path/winpty")
    monkeypatch.setattr(windows.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(windows.sys.stdout, "isatty", lambda: True)
    assert windows.ensure_tty(["cmd"]) == ["cmd"]


def test_ensure_tty_winpty(monkeypatch):
    monkeypatch.setattr(windows.sys, "platform", "win32")
    monkeypatch.setattr(windows.shutil, "which", lambda x: "/path/winpty")
    monkeypatch.setattr(windows.sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr(windows.sys.stdout, "isatty", lambda: False)
    assert windows.ensure_tty(["cmd"]) == ["/path/winpty", "--", "cmd"]
