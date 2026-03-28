#!/usr/bin/env bash
# codesnap setup for Ubuntu 24.04+ (Wayland + GNOME)
# Fixed for GNOME Wayland compatibility
# Version 2.2 with enhanced multi-language OCR

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
echo "║       codesnap installer v2.2        ║"
echo "║   Multi-Language OCR for Wayland     ║"
echo "╚══════════════════════════════════════╝"
echo ""

# Check if running on Wayland
if [[ "$XDG_SESSION_TYPE" != "wayland" ]]; then
    warn "Not running on Wayland. This script is optimized for Wayland."
    warn "If you're on X11, the selection tool may not work properly."
    echo ""
fi

# System deps
step "Installing system packages..."
sudo apt-get update -qq
sudo apt-get install -y \
    grim \
    slurp \
    wl-clipboard \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-osd \
    libnotify-bin \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    curl \
    gnome-screenshot \
    build-essential \
    libtesseract-dev \
    libleptonica-dev

# Check if tesseract-all was installed, if not offer to install more languages
if ! dpkg -l | grep -q tesseract-ocr-all; then
    echo ""
    warn "For better OCR accuracy, consider installing additional languages:"
    echo "   sudo apt install tesseract-ocr-all"
    echo "   (This will install all language packs for better recognition)"
    echo ""
fi

info "System packages installed"

# Check if gnome-screenshot is available (fallback)
if command -v gnome-screenshot &> /dev/null; then
    info "GNOME screenshot tool available (will be used as fallback)"
else
    warn "gnome-screenshot not found - manual coordinate input may be needed"
fi

# uv
step "Setting up uv..."
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
    source "$HOME/.cargo/env" 2>/dev/null || true
fi
info "uv ready"

# Python env
step "Creating uv virtual environment..."
mkdir -p "$APP_DIR"
cd "$APP_DIR"
rm -rf .venv
uv venv --python 3.12
source .venv/bin/activate

# Install Python packages
uv pip install --upgrade pip

info "Installing core packages..."
uv pip install pytesseract pillow numpy autopep8

info "Installing optional packages for enhanced OCR..."
uv pip install scikit-image scipy || warn "Optional packages failed to install (OCR will still work with basic mode)"

# Verify installations
info "Verifying installations..."
python -c "import pytesseract; import PIL; import numpy" 2>/dev/null && info "Core packages OK" || warn "Some core packages missing"

info "Python packages installed"

deactivate

# Copy the Python script
step "Installing codesnap.py..."
if [ -f "$SCRIPT_DIR/codesnap.py" ]; then
    cp "$SCRIPT_DIR/codesnap.py" "$APP_DIR/codesnap.py"
else
    error "codesnap.py not found in $SCRIPT_DIR"
fi
chmod +x "$APP_DIR/codesnap.py"
info "Python script installed to $APP_DIR/codesnap.py"

# Create launcher script
step "Installing codesnap launcher..."
mkdir -p "$INSTALL_DIR"

cat > "$INSTALL_DIR/codesnap" << 'EOF'
#!/usr/bin/env bash
APP_DIR="$HOME/.local/share/codesnap"
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-0}"
export PATH="$HOME/.local/bin:$PATH"
exec "$APP_DIR/.venv/bin/python" "$APP_DIR/codesnap.py" "$@"
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

info "Hotkey registered"

# Check PATH and offer to add if needed
echo ""
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    warn "~/./local/bin not in PATH"
    echo ""
    echo "Add this to your ~/.bashrc or ~/.zshrc:"
    echo '  export PATH="$HOME/.local/bin:$PATH"'
    echo ""
    echo "Then run: source ~/.bashrc (or restart terminal)"
    echo ""
fi

# Final success message
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║ ✅ codesnap v2.2 installed successfully!                 ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "📸 How to use:"
echo "   ${GREEN}Basic usage:${NC}"
echo "   • Press Super + Shift + L"
echo "   • Or run: codesnap"
echo ""
echo "   ${GREEN}Advanced options:${NC}"
echo "   • ${CYAN}codesnap --interactive${NC}    - Edit OCR results before copying"
echo "   • ${CYAN}codesnap --high-quality${NC}   - Enhanced preprocessing (slower but better)"
echo "   • ${CYAN}codesnap --version${NC}        - Show version and installed components"
echo ""
echo "✨ New in v2.2:"
echo "   • Multi-language OCR support"
echo "   • Automatic language detection"
echo "   • Enhanced preprocessing with --high-quality flag"
echo "   • Better code recognition for 10+ languages"
echo ""
echo "🔧 Troubleshooting:"
echo "   • If slurp doesn't work, the script falls back to GNOME screenshot"
echo "   • For better accuracy: codesnap --high-quality"
echo "   • To see what's installed: codesnap --version"
echo ""
echo "Test it now: ${CYAN}codesnap${NC}"
echo ""

# Offer to test the installation
read -p "Do you want to test codesnap now? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    step "Testing codesnap..."
    codesnap --version
    echo ""
    success "Test completed! Try capturing some code with: codesnap"
else
    info "You can test later by running: codesnap"
fi


