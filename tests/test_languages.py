from codesnap.languages import detect_language


def test_detect_python():
    code = "def calculate_total(items):\n    return sum(item.price for item in items)"
    assert detect_language(code) == "python"


def test_detect_javascript():
    code = "const handleClick = (e) => {\n    console.log('clicked', e.target);\n};"
    assert detect_language(code) in ("javascript", "typescript")


def test_detect_typescript():
    code = (
        "interface UserProps {\n"
        "    id: number;\n"
        "    name: string;\n"
        "}\n"
        "const user: UserProps = { id: 1, name: 'Alice' };"
    )
    assert detect_language(code) == "typescript"


def test_detect_rust():
    code = (
        "fn main() -> Result<(), Box<dyn std::error::Error>> {\n"
        '    println!("Hello, world!");\n'
        "    Ok(())\n"
        "}"
    )
    assert detect_language(code) == "rust"


def test_detect_go():
    code = 'package main\n\nimport "fmt"\n\nfunc main() {\n    fmt.Println("Hello Go")\n}'
    assert detect_language(code) == "go"


def test_detect_bash():
    code = '#!/bin/bash\necho "Deploying application..."\nexport ENV=production'
    assert detect_language(code) == "bash"


def test_detect_sql():
    code = "SELECT u.id, u.email FROM users u WHERE u.created_at >= NOW() ORDER BY u.id DESC;"
    assert detect_language(code) == "sql"


def test_detect_html():
    code = (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head><title>App</title></head>\n"
        '<body><div class="container"></div></body></html>'
    )
    assert detect_language(code) == "html"


def test_detect_empty_or_unknown():
    assert detect_language("") == "text"
    assert detect_language("hello world plain text") == "text"
