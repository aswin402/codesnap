"""Command-line interface and main orchestration for codesnap."""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from codesnap import __description__, __version__
from codesnap.capture import REQUIRED_SYSTEM_TOOLS, capture_screen_region, check_system_dependencies
from codesnap.cleaner import clean_code_text
from codesnap.clipboard import copy_to_clipboard, send_notification
from codesnap.exceptions import CaptureCancelledError, CodesnapError
from codesnap.formatters import format_code
from codesnap.languages import detect_language
from codesnap.ocr import check_ocr_dependencies, extract_text_from_image, get_available_engines


def show_version() -> None:
    """Print version and system dependency diagnostic info."""
    print(f"codesnap v{__version__}")
    print(f"Description: {__description__}")
    print(f"Python:      {sys.version.split()[0]}")
    print(f"Platform:    {sys.platform}")
    print("\nSystem tools:")
    for tool in REQUIRED_SYSTEM_TOOLS:
        status = "✓" if shutil.which(tool) else "✗"
        print(f"  {status} {tool}")
    print("\nOCR engines:")
    available_engines = get_available_engines()
    for eng in ["tesseract", "rapidocr"]:
        status = "✓" if eng in available_engines else "✗ (optional)"
        print(f"  {status} {eng}")
    session_type = os.environ.get("XDG_SESSION_TYPE", "unknown")
    print(f"\nSession type: {session_type}")


def interactive_edit(text: str) -> str:
    """Open text in $EDITOR for interactive user review and adjustments."""
    editor = os.environ.get("EDITOR", "nano")
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".txt", delete=False) as tf:
        tf.write(text)
        temp_path = tf.name

    try:
        subprocess.call([editor, temp_path])
        return Path(temp_path).read_text(encoding="utf-8")
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def main(argv: list[str] | None = None) -> int:
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(prog="codesnap", description=__description__)
    parser.add_argument("-v", "--version", action="store_true", help="Show version information")
    parser.add_argument(
        "-i", "--interactive", action="store_true", help="Review and edit extracted text in editor"
    )
    parser.add_argument(
        "-q", "--high-quality", action="store_true", help="Enhanced image preprocessing"
    )
    parser.add_argument("-o", "--output", help="Write extracted code to specified file path")
    parser.add_argument(
        "-c", "--stdout", action="store_true", help="Print extracted code directly to stdout"
    )
    parser.add_argument(
        "-l", "--lang", help="Override detected programming language (e.g. python, rust, sql)"
    )
    parser.add_argument(
        "--engine",
        choices=["auto", "rapidocr", "tesseract"],
        default="auto",
        help="OCR engine: auto (prefers RapidOCR if available), rapidocr, or tesseract",
    )
    parser.add_argument("--no-clipboard", action="store_true", help="Skip copying to clipboard")
    parser.add_argument(
        "image", nargs="?", help="Optional image file to extract code from directly"
    )

    args = parser.parse_args(argv)

    if args.version:
        show_version()
        return 0

    if args.image:
        if not os.path.isfile(args.image):
            print(f"[codesnap] ERROR: File not found: {args.image}", file=sys.stderr)
            return 1
        try:
            check_ocr_dependencies(engine=args.engine)
        except CodesnapError as e:
            send_notification("codesnap error", str(e), icon="dialog-error")
            print(f"[codesnap] ERROR: {e}", file=sys.stderr)
            return 1
    else:
        try:
            check_system_dependencies()
            check_ocr_dependencies(engine=args.engine)
        except CodesnapError as e:
            send_notification("codesnap error", str(e), icon="dialog-error")
            print(f"[codesnap] ERROR: {e}", file=sys.stderr)
            return 1

    with tempfile.TemporaryDirectory(prefix="codesnap_") as tmpdir:
        if args.image:
            img_path = args.image
        else:
            img_path = os.path.join(tmpdir, "snap.png")
            send_notification("codesnap", "Select code area", icon="accessories-screenshot")

            try:
                capture_screen_region(img_path)
            except CaptureCancelledError:
                send_notification("codesnap", "Selection cancelled", icon="dialog-information")
                return 0
            except CodesnapError as e:
                send_notification("codesnap error", str(e), icon="dialog-error")
                print(f"[codesnap] ERROR: {e}", file=sys.stderr)
                return 1

        try:
            raw_text = extract_text_from_image(
                img_path, high_quality=args.high_quality, engine=args.engine
            )
        except CodesnapError as e:
            send_notification("codesnap error", str(e), icon="dialog-error")
            print(f"[codesnap] ERROR: {e}", file=sys.stderr)
            return 1

        if not raw_text.strip():
            send_notification(
                "codesnap", "No text detected in selected area.", icon="dialog-warning"
            )
            print("[codesnap] No text detected. Try capturing a sharper image.", file=sys.stderr)
            return 0

        # Post-process and clean OCR output
        cleaned_text = clean_code_text(raw_text)

        # Detect programming language or use override
        lang = args.lang.lower() if args.lang else detect_language(cleaned_text)

        # Format snippet with ruff if python
        formatted_text = format_code(cleaned_text, lang)

        # Interactive manual edit if requested
        if args.interactive:
            print("\n" + "=" * 60)
            print("Extracted text (pre-edit):")
            print("=" * 60)
            print(formatted_text)
            print("=" * 60)
            answer = input("\nEdit text in editor? [y/N]: ").strip().lower()
            if answer == "y":
                formatted_text = interactive_edit(formatted_text)
                if not args.lang:
                    lang = detect_language(formatted_text)

        # Write to file if -o/--output specified
        if args.output:
            try:
                Path(args.output).write_text(formatted_text, encoding="utf-8")
            except Exception as e:
                print(f"[codesnap] ERROR: Failed to write to {args.output}: {e}", file=sys.stderr)
                return 1

        # Output to stdout if -c/--stdout specified
        if args.stdout:
            print(formatted_text)

        # Copy to clipboard unless disabled
        if not args.no_clipboard:
            try:
                copy_to_clipboard(formatted_text)
            except CodesnapError as e:
                send_notification("codesnap error", str(e), icon="dialog-error")
                print(f"[codesnap] ERROR: {e}", file=sys.stderr)
                return 1

        line_count = len([line for line in formatted_text.splitlines() if line.strip()])
        if not args.stdout:
            send_notification(
                "codesnap ✓", f"{lang.capitalize()} • {line_count} lines copied", icon="edit-copy"
            )
            print(f"[codesnap] Success: {lang} • {line_count} lines processed", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
