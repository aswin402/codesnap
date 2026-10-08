from unittest.mock import patch

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


def test_cli_output_to_file(tmp_path):
    img_file = tmp_path / "dummy.png"
    img_file.write_bytes(b"dummy")
    out_file = tmp_path / "out.py"

    with patch("codesnap.cli.check_system_dependencies"):
        with patch("codesnap.cli.extract_text_from_image", return_value="def foo():\n    return 1"):
            with patch("codesnap.cli.copy_to_clipboard"):
                with patch("codesnap.cli.send_notification"):
                    ret = main([str(img_file), "-o", str(out_file)])
                    assert ret == 0
                    assert out_file.exists()
                    assert "def foo():" in out_file.read_text(encoding="utf-8")


def test_cli_stdout_flag(tmp_path, capsys):
    img_file = tmp_path / "dummy.png"
    img_file.write_bytes(b"dummy")

    with patch("codesnap.cli.check_system_dependencies"):
        with patch("codesnap.cli.extract_text_from_image", return_value="const x = 42;"):
            with patch("codesnap.cli.copy_to_clipboard"):
                with patch("codesnap.cli.send_notification"):
                    ret = main([str(img_file), "-c"])
                    assert ret == 0
                    captured = capsys.readouterr()
                    assert "const x = 42;" in captured.out
