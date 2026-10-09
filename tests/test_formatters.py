from unittest.mock import patch

from codesnap.formatters import _run_formatter, format_code


def test_format_python_code():
    raw_python = "def add(x,y):\n    return x+y\n"
    formatted = format_code(raw_python, lang="python")
    assert "def add(x, y):" in formatted
    assert "return x + y" in formatted


def test_format_python_syntax_error_fallback():
    incomplete = "def broken(:"
    formatted = format_code(incomplete, lang="python")
    assert formatted == incomplete


def test_format_empty_code():
    assert format_code("", lang="python") == ""
    assert format_code(None, lang="python") is None
    assert format_code("print(1)", lang="") == "print(1)"


def test_format_rust_code_mock():
    raw_rust = 'fn main(){println!("hello");}'
    with patch("shutil.which", return_value="/bin/rustfmt"):
        with patch(
            "codesnap.formatters._run_formatter",
            return_value='fn main() {\n    println!("hello");\n}',
        ):
            res = format_code(raw_rust, lang="rust")
            assert '    println!("hello");' in res


def test_format_go_code_mock():
    raw_go = "package main\nfunc main(){\nprintln(1)\n}"
    with patch("shutil.which", return_value="/bin/gofmt"):
        with patch(
            "codesnap.formatters._run_formatter",
            return_value="package main\n\nfunc main() {\n\tprintln(1)\n}",
        ):
            res = format_code(raw_go, lang="go")
            assert "func main() {" in res


def test_format_js_ts_with_biome_mock():
    raw_js = "const x={a:1,b:2};"
    with patch("shutil.which", side_effect=lambda x: "/bin/biome" if x == "biome" else None):
        with patch("codesnap.formatters._run_formatter", return_value="const x = { a: 1, b: 2 };"):
            res = format_code(raw_js, lang="javascript")
            assert res == "const x = { a: 1, b: 2 };"


def test_format_js_ts_with_prettier_fallback_mock():
    raw_ts = "type Foo={bar:string};"
    with patch("shutil.which", side_effect=lambda x: "/bin/prettier" if x == "prettier" else None):
        with patch(
            "codesnap.formatters._run_formatter", return_value="type Foo = {\n  bar: string;\n};"
        ):
            res = format_code(raw_ts, lang="typescript")
            assert "type Foo = {" in res


def test_format_bash_mock():
    raw_sh = "if [ $x -eq 1 ];then echo ok;fi"
    with patch("shutil.which", return_value="/bin/shfmt"):
        with patch(
            "codesnap.formatters._run_formatter",
            return_value="if [ $x -eq 1 ]; then\n    echo ok\nfi",
        ):
            res = format_code(raw_sh, lang="bash")
            assert "echo ok" in res


def test_format_c_cpp_mock():
    raw_cpp = "int main(){int x=1+2;return x;}"
    with patch("shutil.which", return_value="/bin/clang-format"):
        with patch(
            "codesnap.formatters._run_formatter",
            return_value="int main() {\n  int x = 1 + 2;\n  return x;\n}",
        ):
            res = format_code(raw_cpp, lang="cpp")
            assert "int main() {" in res


def test_format_html_css_mock():
    raw_html = "<div class='test'><p>hello</p></div>"
    with patch("shutil.which", return_value="/bin/prettier"):
        with patch(
            "codesnap.formatters._run_formatter",
            return_value='<div class="test">\n  <p>hello</p>\n</div>',
        ):
            res = format_code(raw_html, lang="html")
            assert "<p>hello</p>" in res


def test_format_missing_tools_passthrough():
    raw_code = "fn main() { return 1; }"
    with patch("shutil.which", return_value=None):
        res = format_code(raw_code, lang="rust")
        assert res == raw_code


def test_run_formatter_timeout_handling():
    with patch("subprocess.run", side_effect=Exception("timeout")):
        res = _run_formatter(["dummy-cmd"], "some code")
        assert res is None
