#!/bin/sh
set -e

REPO_URL="https://github.com/dsillman2000/wiki-client.git"
INSTALL_DIR="$HOME/.local/share/wiki-client"
BIN_DIR="$HOME/.local/bin"

info() {
    printf '%s\n' "$*"
}

warn() {
    printf 'warning: %s\n' "$*" >&2
}

die() {
    printf 'error: %s\n' "$*" >&2
    exit 1
}

is_command() {
    command -v "$1" >/dev/null 2>&1
}

check_python() {
    if ! is_command python3; then
        die "python3 is required but not installed"
    fi
    py_version_ok="$(python3 -c 'import sys; print(sys.version_info[:2] >= (3, 10))')"
    if [ "$py_version_ok" != "True" ]; then
        die "Python 3.10 or newer is required (found $(python3 --version))"
    fi
}

check_pip() {
    if ! python3 -m pip --version >/dev/null 2>&1; then
        die "pip is required but not available (try: python3 -m ensurepip)"
    fi
}

check_git() {
    if ! is_command git; then
        die "git is required but not installed"
    fi
}

ensure_local_bin() {
    if [ ! -d "$BIN_DIR" ]; then
        info "Creating $BIN_DIR"
        mkdir -p "$BIN_DIR"
    fi
}

install_repo() {
    if [ -d "$INSTALL_DIR/.git" ]; then
        info "Updating wiki-client in $INSTALL_DIR"
        git -C "$INSTALL_DIR" pull --quiet origin main
    else
        info "Cloning wiki-client to $INSTALL_DIR"
        if [ -e "$INSTALL_DIR" ]; then
            die "path exists but is not a git repository: $INSTALL_DIR"
        fi
        git clone --quiet "$REPO_URL" "$INSTALL_DIR"
    fi
}

install_package() {
    info "Installing wiki-client Python package..."
    python3 -m pip install --quiet --user -e "$INSTALL_DIR"
    info "Installation complete."
}

check_path() {
    case ":$PATH:" in
        *":$BIN_DIR:"*)
            return 0
            ;;
    esac
    return 1
}

verify_install() {
    info "Verifying installation..."
    if ! command -v wiki >/dev/null 2>&1; then
        die "installation verification failed: 'wiki' not found in PATH"
    fi
    info "Installation successful!"
    info ""
    info "wiki version:"
    wiki --version || true
}

main() {
    check_python
    check_pip
    check_git
    ensure_local_bin
    install_repo
    install_package

    if check_path; then
        info "$BIN_DIR is already in your PATH"
    else
        info ""
        info "IMPORTANT: Add $BIN_DIR to your PATH by adding this line to your shell config:"
        info ""
        info "  export PATH=\"\$HOME/.local/bin:\$PATH\""
        info ""
        info "Then reload your shell or run:"
        info "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    fi

    verify_install
}

main "$@"
