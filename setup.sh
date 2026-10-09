#!/usr/bin/env bash
# codesnap setup for Ubuntu 24.04+ (Wayland + GNOME)
# Version 2.4 - Modernized with uv, ruff, and modular architecture

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$HOME/.local/bin"
APP_DIR="$HOME/.local/share/codesnap"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

info() { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}⚠${NC} $*"; }
error() { echo -e "${RED}✗${NC} $*"; exit 1; }
step() { echo -e "\n${CYAN}▸${NC} $*"; }
success() { echo -e "${BLUE}🎉${NC} $*"; }

echo ""
echo "╔══════════════════════════════════════╗"
echo "║       codesnap installer v2.4.4      ║"
echo "║   Fast OCR Code Extractor (Wayland)  ║"
echo "╚══════════════════════════════════════╝"
echo ""

# Check if running on Wayland
if [[ "$XDG_SESSION_TYPE" != "wayland" ]]; then
    warn "Not running on Wayland. This script is optimized for Wayland."
    warn "If you are on X11, clipboard fallback will use xclip if installed."
    echo ""
fi

# System dependencies
step "Installing system packages..."
sudo apt-get update -qq
sudo apt-get install -y \
    grim \
    slurp \
    wl-clipboard \
    gnome-screenshot \
    tesseract-ocr \
    tesseract-ocr-eng \
    libnotify-bin \
    python3 \
    curl \
    git

info "System packages installed"

# Setup uv
step "Setting up uv..."
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"
fi
info "uv ready"

# Determine source location (local repo or piped from curl)
if [ -f "$SCRIPT_DIR/pyproject.toml" ]; then
    INSTALL_SOURCE="$SCRIPT_DIR"
else
    INSTALL_SOURCE="git+https://github.com/aswin402/codesnap.git"
fi

# Python env
step "Creating uv virtual environment and installing codesnap..."
mkdir -p "$APP_DIR"
rm -rf "$APP_DIR/.venv"
uv venv "$APP_DIR/.venv"

VIRTUAL_ENV="$APP_DIR/.venv" uv pip install "$INSTALL_SOURCE"

info "codesnap package and dependencies installed in virtual environment"

# Create launcher script
step "Installing codesnap launcher..."
mkdir -p "$INSTALL_DIR"

cat > "$INSTALL_DIR/codesnap" << 'EOF'
#!/usr/bin/env bash
APP_DIR="$HOME/.local/share/codesnap"
export PATH="$HOME/.local/bin:$PATH"
if [ -t 2 ]; then
    exec "$APP_DIR/.venv/bin/codesnap" "$@"
fi
# Launched without a terminal (e.g. hotkey): keep errors in a log file
LOG_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/codesnap"
mkdir -p "$LOG_DIR"
echo "--- $(date '+%F %T') codesnap $*" >> "$LOG_DIR/codesnap.log"
exec "$APP_DIR/.venv/bin/codesnap" "$@" 2>> "$LOG_DIR/codesnap.log"
EOF

chmod +x "$INSTALL_DIR/codesnap"
info "Launcher installed to $INSTALL_DIR/codesnap"

# Hotkey (GNOME)
step "Registering hotkey Super+Shift+L..."
BINDING_PATH="/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/codesnap/"
EXISTING=$(gsettings get org.gnome.settings-daemon.plugins.media-keys custom-keybindings 2>/dev/null || echo "@as []")

if ! echo "$EXISTING" | grep -q "codesnap"; then
    if [ "$EXISTING" = "@as []" ]; then
        NEW_LIST="['$BINDING_PATH']"
    else
        NEW_LIST="${EXISTING%]}, '$BINDING_PATH']"
    fi
    gsettings set org.gnome.settings-daemon.plugins.media-keys custom-keybindings "$NEW_LIST"
fi

gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:"$BINDING_PATH" name "codesnap"
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:"$BINDING_PATH" command "$INSTALL_DIR/codesnap"
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:"$BINDING_PATH" binding "<Super><Shift>l"

info "Hotkey registered (Super+Shift+L)"

# Check PATH
echo ""
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    warn "$HOME/.local/bin is not in your PATH"
    echo "Add this to your ~/.bashrc or ~/.zshrc:"
    echo '  export PATH="$HOME/.local/bin:$PATH"'
    echo ""
fi

echo "╔══════════════════════════════════════════════════════════╗"
echo "║ ✅ codesnap v2.4.4 installed successfully!               ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "📸 How to use:"
echo "   • Press Super + Shift + L"
echo "   • Or run: codesnap"
echo ""
echo "   Options:"
echo "   • codesnap --interactive   - Review/edit snippet in \$EDITOR before copying"
echo "   • codesnap --high-quality  - Higher resolution upscale"
echo "   • codesnap --version       - Diagnostic info & installed tools"
echo ""
