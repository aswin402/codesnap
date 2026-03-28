#!/usr/bin/env python3
"""
codesnap — Offline code extractor for Ubuntu Wayland (GNOME)
Enhanced with aggressive character correction for code
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
__version__ = "2.3.0"
__author__ = "codesnap"
__description__ = "Offline code extractor for Ubuntu Wayland (GNOME) with aggressive character correction"

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
    
    # Check Python packages
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
        
        # Simple but effective preprocessing
        img = ImageEnhance.Contrast(img).enhance(2.0)
        img = ImageEnhance.Sharpness(img).enhance(2.0)
        
        # Binarize with adaptive threshold
        img_array = np.array(img)
        threshold = np.mean(img_array) * 0.85
        binary = img_array > threshold
        img = Image.fromarray((binary * 255).astype(np.uint8))
        
        # Remove small noise
        img = img.filter(ImageFilter.MedianFilter(size=2))
        
        return img
        
    except Exception as e:
        print(f"[codesnap] Preprocessing error: {e}", file=sys.stderr)
        # Fallback to simple preprocessing
        img = Image.open(img_path).convert("L")
        return img

def aggressive_character_correction(text: str) -> str:
    """Aggressively fix common OCR character misrecognitions"""
    
    # Common word replacements (case insensitive)
    word_replacements = {
        # Python keywords
        r'\belse\b': 'else',
        r'\bels e\b': 'else',
        r'\bels e\b': 'else',
        r'\be1se\b': 'else',
        r'\bif\b': 'if',
        r'\bfor\b': 'for',
        r'\bin\b': 'in',
        r'\bdef\b': 'def',
        r'\bdet\b': 'def',
        r'\bdep\b': 'def',
        r'\bclass\b': 'class',
        r'\bimport\b': 'import',
        r'\bfrom\b': 'from',
        r'\breturn\b': 'return',
        r'\bretum\b': 'return',
        r'\bprint\b': 'print',
        r'\bpriot\b': 'print',
        r'\bprinr\b': 'print',
        r'\bTrue\b': 'True',
        r'\bFalse\b': 'False',
        r'\bNone\b': 'None',
        
        # Common words in messages
        r'\binfo\b': 'info',
        r'\b1nfo\b': 'info',
        r'\byou\b': 'you',
        r'\by0u\b': 'you',
        r'\byou\b': 'you',
        r'\btest\b': 'test',
        r'\bte st\b': 'test',
        r'\blater\b': 'later',
        r'\bl ater\b': 'later',
        r'\brunning\b': 'running',
        r'\brunn1ng\b': 'running',
        r'\bcodesnap\b': 'codesnap',
        r'\bc0desnap\b': 'codesnap',
        r'\bcode snap\b': 'codesnap',
    }
    
    # Apply word replacements
    result = text
    for pattern, replacement in word_replacements.items():
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    
    # Character-level fixes
    char_fixes = [
        ('1', 'l'),  # 1 to l (common in text)
        ('0', 'o'),  # 0 to o (common in text)
        ('5', 's'),  # 5 to s
        ('8', 'b'),  # 8 to b
        ('2', 'z'),  # 2 to z
        ('4', 'a'),  # 4 to a
        ('3', 'e'),  # 3 to e
    ]
    
    # Apply character fixes carefully (only in context)
    lines = result.split('\n')
    fixed_lines = []
    
    for line in lines:
        # Don't modify numbers in code contexts
        if re.search(r'[0-9][=<>!]', line) or re.search(r'[=<>!][0-9]', line):
            # Likely contains numbers in code, be careful
            fixed_lines.append(line)
            continue
        
        # Apply fixes
        fixed_line = line
        for old, new in char_fixes:
            # Only replace if it looks like text, not numbers
            if re.search(r'\b' + old + r'[a-z]', line, re.IGNORECASE) or \
               re.search(r'[a-z]' + old + r'\b', line, re.IGNORECASE):
                fixed_line = fixed_line.replace(old, new)
        
        fixed_lines.append(fixed_line)
    
    return '\n'.join(fixed_lines)

def run_ocr(img_path: str, high_quality: bool = False) -> str:
    """Run OCR with improved configuration"""
    try:
        img = preprocess_image(img_path, high_quality)
        
        # Try multiple OCR configurations
        configs = [
            '--oem 3 --psm 6',  # Default - single uniform block of text
            '--oem 3 --psm 7',  # Single text line
            '--oem 1 --psm 6',  # Legacy engine
        ]
        
        best_text = ""
        best_score = 0
        
        for config in configs:
            try:
                text = pytesseract.image_to_string(img, config=config, lang='eng')
                if text.strip():
                    # Score based on alphanumeric content and common patterns
                    score = len(re.findall(r'[a-zA-Z0-9_]+', text))
                    # Bonus for code-like patterns
                    if re.search(r'\b(def|class|import|if|else|for)\b', text):
                        score += 20
                    if re.search(r'[=<>!]', text):
                        score += 10
                    
                    if score > best_score:
                        best_score = score
                        best_text = text
            except Exception:
                continue
        
        if best_text:
            return best_text
        else:
            # Ultimate fallback
            return pytesseract.image_to_string(img, lang='eng')
            
    except Exception as e:
        print(f"[codesnap] OCR error: {e}", file=sys.stderr)
        return ""

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

# ─── language detection ────────────────────────────────────────────────────
LANG_HINTS: Dict[str, list[str]] = {
    'python': [r'\bdef\b', r'\bimport\b', r':\s*$', r'\bself\b', r'print\('],
    'javascript': [r'\bconst\b', r'\blet\b', r'=>', r'console\.', r'function\s*\('],
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
        raw_text = run_ocr(img_path, args.high_quality)

        if not raw_text.strip():
            notify("codesnap", "No text found in the selected area.", "dialog-warning")
            print("[codesnap] No text detected. Try selecting a larger area with clear text.", file=sys.stderr)
            sys.exit(0)

        # Apply aggressive character correction
        corrected_text = aggressive_character_correction(raw_text)
        
        if args.interactive:
            print("\n" + "="*60)
            print("OCR RESULT (after correction):")
            print("="*60)
            print(corrected_text)
            print("="*60)
            response = input("\nEdit text? [y/N]: ").strip().lower()
            if response == 'y':
                with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as f:
                    f.write(corrected_text)
                    temp_path = f.name
                editor = os.environ.get('EDITOR', 'nano')
                subprocess.call([editor, temp_path])
                with open(temp_path, 'r') as f:
                    corrected_text = f.read()
                os.unlink(temp_path)
        
        lang = detect_language(corrected_text)
        
        copy_to_clipboard(corrected_text)
        
        line_count = sum(1 for line in corrected_text.split('\n') if line.strip())
        
        notify("codesnap ✓", f"{lang.capitalize()} • {line_count} lines copied", "edit-copy")
        print(f"[codesnap] Success: {lang} • {line_count} lines", file=sys.stderr)
        
        # Preview the corrected text
        preview = corrected_text[:200] + "..." if len(corrected_text) > 200 else corrected_text
        print(f"\n[codesnap] Preview:\n{preview}\n", file=sys.stderr)

if __name__ == '__main__':
    main()
    
    

