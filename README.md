# codesnap

Offline code extractor for Ubuntu (Wayland). Press a hotkey, draw a box around
any code on screen — YouTube video, tutorial, PDF — and the cleaned, formatted
code is instantly on your clipboard.

## Requirements

- Ubuntu 23.04+ (Wayland / GNOME)
- Python 3.8+
- No internet needed after install

## Install

```bash
git clone <this-repo>   # or just download the folder
cd codesnap
chmod +x setup.sh
./setup.sh
codesnap --version
codesnap
```

The setup script installs: `grim`, `slurp`, `tesseract-ocr`, `wl-clipboard`,
`libnotify-bin`, and the `autopep8` Python formatter.

## Usage

1. Press **Super + Shift + L**
2. Your cursor becomes a crosshair — click and drag to select the code region
3. Release — codesnap extracts and cleans the code
4. A notification confirms: `Python • 12 lines • Ctrl+V ready`
5. Paste anywhere with **Ctrl+V**

## How it works

```
Super+Shift+L
     │
     ▼
slurp  ──→  select screen region (crosshair UI)
     │
     ▼
grim   ──→  screenshot that region  →  temp .png
     │
     ▼
tesseract ──→  OCR with --psm 6 (uniform text block)
     │
     ▼
clean  ──→  fix OCR noise (| vs l, indentation, stray chars)
     │
     ▼
detect ──→  identify language (Python, JS, Bash, etc.)
     │
     ▼
format ──→  autopep8 for Python, passthrough for others
     │
     ▼
wl-copy ──→  clipboard
     │
     ▼
notify-send ──→  "Code copied!"
```

## Supported Languages (auto-detected)

Python, JavaScript, TypeScript, Bash, Java, C, C++, Rust, Go, SQL, HTML, CSS

## Tips

- **Zoom in** on the video before snapping — bigger text = better OCR accuracy
- **Pause the video** so text is sharp and not motion-blurred
- Include a little padding around the code block when selecting
- Works on any app: browser, PDF viewer, terminal, VS Code screenshots

## Uninstall

```bash
rm -rf ~/.local/share/codesnap
rm ~/.local/bin/codesnap
```

Then remove the hotkey in **Settings → Keyboard → Custom Shortcuts**.

## Files

```
codesnap/
├── codesnap.py   — main script
├── setup.sh      — installer + hotkey registration
└── README.md     — this file
```

