"""
codesnap — Offline code extractor for Ubuntu Wayland (GNOME)
Fixed: Works with GNOME Wayland (no layer_shell dependency)
"""

import subprocess
import sys
import os
import re
import tempfile
import argparse
from pathlib import Path
from typing import Dict

try:
    from PIL import Image, ImageEnhance, ImageFilter
    import pytesseract
except ImportError:
    print("[codesnap] Error: Missing pytesseract or Pillow in venv.")
    sys.exit(1)

# ─── version information ────────────────────────────────────────────────────
__version__ = "2.0.0"
__author__ = "codesnap"
__description__ = "Offline code extractor for Ubuntu Wayland (GNOME)"

def print_logo():
    print("\n" + "="*60)
    print("                     C O D E S N A P")
    print("          Offline Code Extractor for Ubuntu Wayland")
    print(f"                          v{__version__}")
    print("="*60 + "\n")


def show_version():
    """Display version information with logo"""
    print(print_logo())
    print(f"\n  Version:     {__version__}")
    print(f"  Author:      {__author__}")
    print(f"  Description: {__description__}")
    print(f"  License:     MIT")
    print(f"  Python:      {sys.version.split()[0]}")
    print(f"  Platform:    {sys.platform}")
    
    # Check for required tools
    tools = {
        "grim": False,
        "slurp": False,
        "wl-copy": False,
        "tesseract": False,
        "gnome-screenshot": False
    }
    
    for tool in tools:
        if shutil.which(tool):
            tools[tool] = True
    
    print("\n  Installed tools:")
    for tool, installed in tools.items():
        status = "✓" if installed else "✗"
        print(f"    {status} {tool}")
    
    # Check Wayland
    wayland = os.environ.get("XDG_SESSION_TYPE") == "wayland"
    print(f"\n  Session:      {'Wayland ✓' if wayland else 'X11'}")
    
    sys.exit(0)


# ─── helpers ────────────────────────────────────────────────────────────────
def notify(title: str, body: str, icon: str = "dialog-information") -> None:
    try:
        subprocess.run(
            ["notify-send", "-i", icon, "-t", "4000", title, body],
            check=False, capture_output=True
        )
    except FileNotFoundError:
        pass


def die(msg: str) -> None:
    notify("codesnap error", msg, "dialog-error")
    print(f"[codesnap] ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def check_deps() -> None:
    missing = [cmd for cmd in ("grim", "slurp", "wl-copy") if not shutil.which(cmd)]
    if missing:
        die(f"Missing tools: {', '.join(missing)}\nRun: sudo apt install grim slurp wl-clipboard")


import shutil


# ─── Multiple capture methods for GNOME Wayland ──────────────────────────
def capture_with_gnome_screenshot(tmp_img: str) -> bool:
    """Use GNOME's built-in screenshot tool (works in Wayland)"""
    try:
        print("[codesnap] Using GNOME screenshot tool...", file=sys.stderr)
        notify("codesnap", "Click 'Select Area to Grab' in the screenshot tool", "accessories-screenshot")
        
        result = subprocess.run(
            ["gnome-screenshot", "-a", "-f", tmp_img],
            timeout=60
        )
        return result.returncode == 0 and os.path.exists(tmp_img)
    except Exception as e:
        print(f"[codesnap] GNOME screenshot failed: {e}", file=sys.stderr)
        return False


def capture_with_slurp(tmp_img: str) -> bool:
    """Try slurp with various options"""
    try:
        print("[codesnap] Trying slurp...", file=sys.stderr)
        slurp = subprocess.run(
            ["slurp"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if slurp.returncode == 0 and slurp.stdout.strip():
            geometry = slurp.stdout.strip()
            subprocess.run(["grim", "-g", geometry, tmp_img], check=True)
            return os.path.exists(tmp_img)
    except:
        pass
    
    # Try with format flag
    try:
        slurp = subprocess.run(
            ["slurp", "-f", "%x,%y %wx%h"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if slurp.returncode == 0 and slurp.stdout.strip():
            geometry = slurp.stdout.strip()
            subprocess.run(["grim", "-g", geometry, tmp_img], check=True)
            return os.path.exists(tmp_img)
    except:
        pass
    
    return False


def capture_manual(tmp_img: str) -> bool:
    """Manual coordinate input as last resort"""
    try:
        print("\n[codesnap] Manual coordinate selection required", file=sys.stderr)
        print("Enter coordinates in format: X,Y WIDTH HEIGHT", file=sys.stderr)
        print("Example: 100,100 800,600", file=sys.stderr)
        print("(You can get coordinates using: slurp -o)", file=sys.stderr)
        
        coords = input("Coordinates: ").strip()
        if not coords:
            return False
            
        # Parse coordinates
        match = re.match(r'(\d+)[,\s]+(\d+)[,\s]+(\d+)[,\s]+(\d+)', coords)
        if not match:
            print("[codesnap] Invalid coordinate format", file=sys.stderr)
            return False
            
        x, y, w, h = map(int, match.groups())
        geometry = f"{x},{y} {w}x{h}"
        
        subprocess.run(
            ["grim", "-g", geometry, tmp_img],
            check=True,
            capture_output=True
        )
        return os.path.exists(tmp_img)
        
    except Exception as e:
        print(f"[codesnap] Manual selection error: {e}", file=sys.stderr)
        return False


def capture_region(tmp_img: str) -> bool:
    """Try multiple capture methods until one works"""
    
    # Method 1: Try slurp first
    if capture_with_slurp(tmp_img):
        return True
    
    # Method 2: Try GNOME screenshot
    if shutil.which("gnome-screenshot") and capture_with_gnome_screenshot(tmp_img):
        return True
    
    # Method 3: Manual coordinates
    print("[codesnap] Automatic selection failed. Falling back to manual input.", file=sys.stderr)
    return capture_manual(tmp_img)


# ─── OCR with preprocessing ────────────────────────────────────────────────
def preprocess_image(img_path: str) -> Image.Image:
    img = Image.open(img_path).convert("L")
    img = ImageEnhance.Contrast(img).enhance(2.3)
    img = ImageEnhance.Sharpness(img).enhance(2.8)
    img = img.filter(ImageFilter.MedianFilter(size=3))
    return img


def run_ocr(img_path: str) -> str:
    try:
        img = preprocess_image(img_path)
        config = r'--oem 3 --psm 6 -l eng -c tessedit_char_blacklist=|©®™'
        text = pytesseract.image_to_string(img, config=config)
        return text
    except Exception as e:
        die(f"OCR failed: {e}")


# ─── clean text ────────────────────────────────────────────────────────────
OCR_FIXES = [
    (r'(?<=[a-zA-Z0-9])[\|l](?=[a-zA-Z0-9])', 'I'),
    (r'\b[Ii](?=[0-9])', '1'),
    (r'(?<=[0-9])[Ii]\b', '1'),
    (r'(?<=\s)[Oo](?=\s)', '0'),
    (r'\b0(?=[a-zA-Z])', 'O'),
    (r'»', '>>'), (r'«', '<<'),
    (r'—', '--'), (r'\u2013', '-'), (r'\u2014', '--'),
    (r'\u2018|\u2019', "'"), (r'\u201c|\u201d', '"'),
    (r'[`´]', "'"),
    (r'(?m)^[^\w\s#/\-*+=<>{}()\[\]\"\'`.:,;!@$%^&|\\~?]{1,2}$', ''),
    (r' {3,}', '  '),
]


def clean_ocr(raw: str) -> str:
    if not raw:
        return ""
    text = raw.strip()
    for pattern, repl in OCR_FIXES:
        text = re.sub(pattern, repl, text)

    text = text.replace('\r\n', '\n').replace('\r', '\n')
    lines = [line.rstrip() for line in text.split('\n')]

    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()

    return '\n'.join(lines)


# ─── language detection ────────────────────────────────────────────────────
LANG_HINTS: Dict[str, list[str]] = {
    'python': [r'\bdef\b', r'\bimport\b', r':\s*$', r'\bself\b'],
    'javascript': [r'\bconst\b', r'\blet\b', r'=>', r'console\.'],
    'typescript': [r':\s*(string|number|boolean)', r'\binterface\b'],
    'java': [r'\bpublic\b', r'\bclass\b'],
    'cpp': [r'#include', r'\bstd::'],
    'bash': [r'^#!/', r'\becho\b'],
}


def detect_language(code: str) -> str:
    if not code or not code.strip():
        return 'text'
    scores: Dict[str, int] = {}
    for lang, patterns in LANG_HINTS.items():
        score = sum(1 for p in patterns if re.search(p, code, re.MULTILINE | re.IGNORECASE))
        if score > 0:
            scores[lang] = score
    return max(scores, key=scores.get) if scores else 'text'


# ─── formatter & clipboard ─────────────────────────────────────────────────
def format_code(code: str, lang: str) -> str:
    venv_bin = Path.home() / ".local/share/codesnap/.venv/bin"
    if lang == 'python' and (venv_bin / "autopep8").exists():
        try:
            result = subprocess.run(
                [str(venv_bin / "autopep8"), '--max-line-length', '88', '-'],
                input=code, capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout
        except Exception:
            pass
    return code


def copy_to_clipboard(text: str) -> None:
    try:
        subprocess.run(['wl-copy'], input=text.encode('utf-8'), check=True)
    except Exception as e:
        die(f"Clipboard failed: {e}")


# ─── main ──────────────────────────────────────────────────────────────────
def main() -> None:
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description=__description__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                 # Run normally with selection UI
  %(prog)s --version       # Show version information
  %(prog)s --help          # Show this help message
        """
    )
    parser.add_argument(
        '-v', '--version',
        action='store_true',
        help='Show version information and exit'
    )
    
    args = parser.parse_args()
    
    if args.version:
        show_version()
    
    # Normal execution
    check_deps()

    with tempfile.TemporaryDirectory(prefix='codesnap_') as tmpdir:
        img_path = os.path.join(tmpdir, 'snap.png')

        notify("codesnap", "Select code area", "accessories-screenshot")

        if not capture_region(img_path):
            notify("codesnap", "Selection failed or cancelled", "dialog-warning")
            sys.exit(0)

        if not os.path.exists(img_path):
            die("Failed to capture screenshot.")

        raw_text = run_ocr(img_path)

        if not raw_text.strip():
            notify("codesnap", "No text found in the selected area.", "dialog-warning")
            sys.exit(0)

        clean = clean_ocr(raw_text)
        lang = detect_language(clean)
        formatted = format_code(clean, lang)

        copy_to_clipboard(formatted)

        line_count = sum(1 for line in formatted.split('\n') if line.strip())

        notify(
            "codesnap ✓",
            f"{lang.capitalize()} • {line_count} lines copied",
            "edit-copy"
        )
        print(f"[codesnap] Success: {lang} • {line_count} lines")


if __name__ == '__main__':
    main()