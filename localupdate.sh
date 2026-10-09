#!/usr/bin/env bash
# codesnap - Local In-Place Update Script
# Updates an existing local codesnap installation without re-running system package managers.

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
echo "║       codesnap local updater         ║"
echo "║       In-Place System Upgrade        ║"
echo "╚══════════════════════════════════════╝"
echo ""

# Ensure uv is in PATH
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

if ! command -v uv &> /dev/null; then
    step "Installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
fi
info "uv detected: $(command -v uv)"

# Ensure directories exist
mkdir -p "$INSTALL_DIR"
mkdir -p "$APP_DIR"

step "Updating Python virtual environment in $APP_DIR/.venv..."
# If .venv does not exist or needs refresh, ensure clean venv
if [ ! -d "$APP_DIR/.venv" ]; then
    uv venv "$APP_DIR/.venv"
fi

# Install / update current package into the application venv
VIRTUAL_ENV="$APP_DIR/.venv" uv pip install --upgrade "$SCRIPT_DIR"
VIRTUAL_ENV="$APP_DIR/.venv" uv pip uninstall -y numpy &>/dev/null || true

# Clean up legacy root script if present in APP_DIR to prevent stale code execution
if [ -f "$APP_DIR/codesnap.py" ]; then
    cp "$SCRIPT_DIR/codesnap.py" "$APP_DIR/codesnap.py"
fi

info "Installed updated codesnap package and dependencies into $APP_DIR/.venv"

# Update launcher script
step "Updating launcher script in $INSTALL_DIR/codesnap..."
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
info "Launcher updated: $INSTALL_DIR/codesnap"

# Verify GNOME hotkey registration
step "Checking GNOME keybinding..."
BINDING_PATH="/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/codesnap/"
if command -v gsettings &> /dev/null; then
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
    info "GNOME shortcut verified (Super+Shift+L)"
else
    warn "gsettings not found; skipping GNOME hotkey verification"
fi

# Verification
step "Verifying updated installation..."
"$INSTALL_DIR/codesnap" --version

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║ ✅ codesnap successfully updated to the latest version!   ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "You can now use Super + Shift + L or run: codesnap"
echo ""
