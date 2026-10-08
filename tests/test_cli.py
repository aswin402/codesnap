from codesnap.cli import main


def test_cli_version_flag(capsys):
    ret = main(["--version"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "codesnap v" in captured.out
    assert "System tools:" in captured.out


def test_cli_nonexistent_image(capsys):
    ret = main(["/path/to/nonexistent/file.png"])
    assert ret == 1
    captured = capsys.readouterr()
    assert "File not found" in captured.err
