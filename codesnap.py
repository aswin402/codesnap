#!/usr/bin/env python3
"""
codesnap — Offline code extractor for Ubuntu Wayland (GNOME)
Enhanced with multi-language OCR support and better code recognition
"""

import subprocess
import sys
import os
import re
import tempfile
import argparse
import shutil
from pathlib import Path
from typing import Dict, Optional, Tuple

try:
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps
    import pytesseract
    import numpy as np
except ImportError as e:
    print(f"[codesnap] Error: Missing required package: {e}", file=sys.stderr)
    print("[codesnap] Please run: pip install pillow pytesseract numpy", file=sys.stderr)
    sys.exit(1)

# Try to import optional packages for enhanced preprocessing
HAS_SKIMAGE = False
HAS_SCIPY = False
try:
    from skimage.filters import threshold_local
    HAS_SKIMAGE = True
except ImportError:
    pass

try:
    from scipy.ndimage import gaussian_filter
    HAS_SCIPY = True
except ImportError:
    pass

# ─── version information ────────────────────────────────────────────────────
__version__ = "2.2.1"
__author__ = "codesnap"
__description__ = "Offline code extractor for Ubuntu Wayland (GNOME) with multi-language OCR"

# ─── Language configuration for OCR ─────────────────────────────────────────
def get_installed_tesseract_langs():
    """Get list of installed Tesseract languages"""
    try:
        result = subprocess.run(['tesseract', '--list-langs'], capture_output=True, text=True)
        if result.returncode == 0:
            return [l.strip() for l in result.stdout.split('\n')[1:] if l.strip()]
    except:
        pass
    return []

# ─── OCR character mapping for common mistakes ─────────────────────────────
CHAR_MAP = {
    # Numbers and letters confusion
    '0': 'O', 'O': '0',
    '1': 'I', 'I': '1',  # Fixed: '1' to 'I' is common
    '5': 'S', 'S': '5',
    '8': 'B', 'B': '8',
    '2': 'Z', 'Z': '2',
    '6': 'G', 'G': '6',
    '9': 'g', 'g': '9',
    
    # Punctuation
    ';': ':', ':': ';',
    ',': '.', '.': ',',
    "'": '"', '"': "'",
    '`': "'", '´': "'",
    '’': "'", '‘': "'",
    '“': '"', '”': '"',
    
    # Code-specific
    '(': '{', '{': '(',
    ')': '}', '}': ')',
    '<': '[', '[': '<',
    '>': ']', ']': '>',
    '|': 'I', 'I': '|',
}

# Common OCR misreadings of code keywords (expanded)
KEYWORD_FIXES = {
    # Python
    r'\bdet\b': 'def',
    r'\bdep\b': 'def',
    r'\bclass\b': 'class',
    r'\bimpart\b': 'import',
    r'\bfromm\b': 'from',
    r'\bretum\b': 'return',
    r'\breturrn\b': 'return',
    r'\bpriot\b': 'print',
    r'\bprinr\b': 'print',
    r'\bif\b': 'if',
    r'\belse\b': 'else',
    r'\belif\b': 'elif',
    r'\bwhile\b': 'while',
    r'\bfor\b': 'for',
    r'\bin\b': 'in',
    r'\bTrue\b': 'True',
    r'\bFalse\b': 'False',
    r'\bNone\b': 'None',
    
    # JavaScript/TypeScript
    r'\bconsi\b': 'const',
    r'\bcont\b': 'const',
    r'\blet\b': 'let',
    r'\bfuncrion\b': 'function',
    r'\bexporr\b': 'export',
    r'\bimporr\b': 'import',
    r'\basync\b': 'async',
    r'\bawait\b': 'await',
    r'\btry\b': 'try',
    r'\bcatch\b': 'catch',
    
    # Java/C++
    r'\bpublic\b': 'public',
    r'\bprivate\b': 'private',
    r'\bprotecred\b': 'protected',
    r'\bvoid\b': 'void',
    r'\bint\b': 'int',
    r'\bstring\b': 'String',
    r'\bboolean\b': 'boolean',
    r'\btrue\b': 'true',
    r'\bfalse\b': 'false',
    
    # Common
    r'\bnulll\b': 'null',
    r'\bundefrned\b': 'undefined',
    r'\bNaN\b': 'NaN',
}

def print_logo():
    print("\n" + "="*60)
    print("                     C O D E S N A P")
    print("          Offline Code Extractor for Ubuntu Wayland")
    print(f"                          v{__version__}")
    print("="*60 + "\n")

def show_version():
    """Display version information with logo"""
    print_logo()
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
    
    # Check Tesseract languages
    langs = get_installed_tesseract_langs()
    if langs:
        print(f"\n  Tesseract languages: {len(langs)} installed")
        print(f"    {', '.join(langs[:10])}" + ("..." if len(langs) > 10 else ""))
    
    # Check Python packages - FIXED detection
    packages = {
        "Pillow": False,
        "numpy": False,
        "scikit-image": False,
        "scipy": False
    }
    
    try:
        import PIL
        packages["Pillow"] = True
    except ImportError:
        pass
    
    try:
        import numpy
        packages["numpy"] = True
    except ImportError:
        pass
    
    try:
        import skimage
        packages["scikit-image"] = True
    except ImportError:
        pass
    
    try:
        import scipy
        packages["scipy"] = True
    except ImportError:
        pass
    
    print("\n  Python packages:")
    for pkg, installed in packages.items():
        status = "✓" if installed else "✗"
        print(f"    {status} {pkg}")
    
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

# ─── Enhanced image preprocessing ──────────────────────────────────────────
def preprocess_image(img_path: str, high_quality: bool = False) -> Image.Image:
    """Enhanced preprocessing for better OCR accuracy"""
    try:
        img = Image.open(img_path)
        
        # Convert to grayscale
        img = img.convert("L")
        
        # Increase resolution if too small
        width, height = img.size
        if width < 1000 or height < 300:
            scale_factor = max(1000 / width, 300 / height)
            new_size = (int(width * scale_factor), int(height * scale_factor))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        if high_quality:
            # Apply multiple preprocessing steps
            img = ImageEnhance.Contrast(img).enhance(2.5)
            img = ImageEnhance.Sharpness(img).enhance(3.0)
            
            # Simple thresholding (more reliable)
            img_array = np.array(img)
            threshold = np.mean(img_array) * 0.8  # Adjusted threshold
            binary = img_array > threshold
            img = Image.fromarray((binary * 255).astype(np.uint8))
            
            # Remove noise
            img = img.filter(ImageFilter.MedianFilter(size=3))
        
        return img
        
    except Exception as e:
        print(f"[codesnap] Preprocessing error: {e}", file=sys.stderr)
        # Fallback to simple preprocessing
        img = Image.open(img_path).convert("L")
        return img

def run_ocr(img_path: str, high_quality: bool = False) -> Tuple[str, str]:
    """Run OCR with improved configuration"""
    try:
        img = preprocess_image(img_path, high_quality)
        
        # Try multiple OCR configurations
        configs = [
            ('--oem 3 --psm 6', 'eng'),  # Default
            ('--oem 3 --psm 7', 'eng'),  # Single text line
            ('--oem 3 --psm 8', 'eng'),  # Single word
            ('--oem 1 --psm 6', 'eng'),  # Legacy engine
        ]
        
        best_text = ""
        best_score = 0
        
        for config, lang in configs:
            try:
                text = pytesseract.image_to_string(img, config=config, lang=lang)
                if text.strip():
                    # Score based on alphanumeric content
                    score = len(re.findall(r'[a-zA-Z0-9_]+', text))
                    if score > best_score:
                        best_score = score
                        best_text = text
            except Exception:
                continue
        
        if best_text:
            return best_text, 'eng'
        else:
            # Ultimate fallback
            text = pytesseract.image_to_string(img, lang='eng')
            return text, 'eng'
            
    except Exception as e:
        print(f"[codesnap] OCR error: {e}", file=sys.stderr)
        return "", 'eng'

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
        return result.returncode == 0 and os.path.exists(tmp_img) and os.path.getsize(tmp_img) > 0
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
            result = subprocess.run(["grim", "-g", geometry, tmp_img], capture_output=True)
            return result.returncode == 0 and os.path.exists(tmp_img) and os.path.getsize(tmp_img) > 0
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
            result = subprocess.run(["grim", "-g", geometry, tmp_img], capture_output=True)
            return result.returncode == 0 and os.path.exists(tmp_img) and os.path.getsize(tmp_img) > 0
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
            
        match = re.match(r'(\d+)[,\s]+(\d+)[,\s]+(\d+)[,\s]+(\d+)', coords)
        if not match:
            print("[codesnap] Invalid coordinate format", file=sys.stderr)
            return False
            
        x, y, w, h = map(int, match.groups())
        geometry = f"{x},{y} {w}x{h}"
        
        result = subprocess.run(
            ["grim", "-g", geometry, tmp_img],
            capture_output=True
        )
        return result.returncode == 0 and os.path.exists(tmp_img) and os.path.getsize(tmp_img) > 0
        
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

# ─── clean text ────────────────────────────────────────────────────────────
def clean_ocr(raw: str) -> str:
    """Clean and fix OCR output"""
    if not raw:
        return ""
    
    # Apply keyword fixes
    text = raw
    for pattern, replacement in KEYWORD_FIXES.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    # Fix common character issues
    text = re.sub(r'[|l]', 'I', text)
    text = re.sub(r'[Oo]', '0', text)
    text = re.sub(r'[Ii]', '1', text)
    
    # Fix line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    lines = [line.rstrip() for line in text.split('\n')]
    
    # Remove empty lines at start and end
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    
    return '\n'.join(lines)

# ─── language detection ────────────────────────────────────────────────────
LANG_HINTS: Dict[str, list[str]] = {
    'python': [r'\bdef\b', r'\bimport\b', r':\s*$', r'\bself\b', r'print\('],
    'javascript': [r'\bconst\b', r'\blet\b', r'=>', r'console\.', r'function\s*\('],
    'typescript': [r':\s*(string|number|boolean)', r'\binterface\b'],
    'java': [r'\bpublic\b', r'\bclass\b', r'\bSystem\.out\.'],
    'cpp': [r'#include', r'\bstd::', r'\bint main\b'],
    'bash': [r'^#!/', r'\becho\b', r'\bexport\b'],
}

def detect_language(code: str) -> str:
    """Detect programming language from code"""
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
    """Format code based on language"""
    return code  # Simplified for now

def copy_to_clipboard(text: str) -> None:
    """Copy text to clipboard using wl-copy"""
    try:
        subprocess.run(['wl-copy'], input=text.encode('utf-8'), check=True)
    except Exception as e:
        if shutil.which('xclip'):
            try:
                subprocess.run(['xclip', '-selection', 'clipboard'], input=text.encode('utf-8'), check=True)
            except Exception:
                die(f"Clipboard failed: {e}")
        else:
            die(f"Clipboard failed: {e}")

# ─── main ──────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description=__description__)
    parser.add_argument('-v', '--version', action='store_true', help='Show version information')
    parser.add_argument('-i', '--interactive', action='store_true', help='Allow manual correction')
    parser.add_argument('-q', '--high-quality', action='store_true', help='Enhanced preprocessing')
    
    args = parser.parse_args()
    
    if args.version:
        show_version()
    
    check_deps()

    with tempfile.TemporaryDirectory(prefix='codesnap_') as tmpdir:
        img_path = os.path.join(tmpdir, 'snap.png')

        notify("codesnap", "Select code area", "accessories-screenshot")
        print("[codesnap] Please select the code area...", file=sys.stderr)

        if not capture_region(img_path):
            notify("codesnap", "Selection failed or cancelled", "dialog-warning")
            sys.exit(0)

        if not os.path.exists(img_path) or os.path.getsize(img_path) == 0:
            die("Failed to capture screenshot.")

        print("[codesnap] Processing image...", file=sys.stderr)
        raw_text, detected_lang = run_ocr(img_path, args.high_quality)

        if not raw_text.strip():
            notify("codesnap", "No text found in the selected area.", "dialog-warning")
            print("[codesnap] No text detected. Try selecting a larger area with clear text.", file=sys.stderr)
            sys.exit(0)

        clean = clean_ocr(raw_text)
        
        if args.interactive:
            print("\n" + "="*60)
            print("OCR RESULT:")
            print("="*60)
            print(clean)
            print("="*60)
            response = input("\nEdit text? [y/N]: ").strip().lower()
            if response == 'y':
                with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as f:
                    f.write(clean)
                    temp_path = f.name
                editor = os.environ.get('EDITOR', 'nano')
                subprocess.call([editor, temp_path])
                with open(temp_path, 'r') as f:
                    clean = f.read()
                os.unlink(temp_path)
        
        lang = detect_language(clean)
        formatted = format_code(clean, lang)

        copy_to_clipboard(formatted)

        line_count = sum(1 for line in formatted.split('\n') if line.strip())

        notify("codesnap ✓", f"{lang.capitalize()} • {line_count} lines copied", "edit-copy")
        print(f"[codesnap] Success: {lang} • {line_count} lines", file=sys.stderr)

if __name__ == '__main__':
    main()