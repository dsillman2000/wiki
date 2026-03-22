#!/bin/sh
set -e

REPO_URL="https://github.com/dsillman2000/wiki.git"
INSTALL_DIR="$HOME/.local/share/wiki-cli"
BIN_DIR="$HOME/.local/bin"
BIN_PATH="$BIN_DIR/wiki"

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

check_curl() {
    if ! is_command curl; then
        die "curl is required but not installed"
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
        info "Updating wiki-cli in $INSTALL_DIR"
        git -C "$INSTALL_DIR" pull --quiet origin main
    else
        info "Cloning wiki-cli to $INSTALL_DIR"
        if [ -e "$INSTALL_DIR" ]; then
            die "path exists but is not a git repository: $INSTALL_DIR"
        fi
        git clone --quiet "$REPO_URL" "$INSTALL_DIR"
    fi
}

create_symlink() {
    if [ -L "$BIN_PATH" ]; then
        existing_target="$(readlink "$BIN_PATH")"
        if [ "$existing_target" = "$INSTALL_DIR/wiki" ]; then
            info "Symlink already exists: $BIN_PATH -> $INSTALL_DIR/wiki"
            return 0
        fi
        info "Updating symlink: $BIN_PATH -> $INSTALL_DIR/wiki"
        rm "$BIN_PATH"
    elif [ -e "$BIN_PATH" ]; then
        info "Backing up existing file: $BIN_PATH -> $BIN_PATH.bak"
        mv "$BIN_PATH" "$BIN_PATH.bak"
    fi
    info "Creating symlink: $BIN_PATH -> $INSTALL_DIR/wiki"
    ln -s "$INSTALL_DIR/wiki" "$BIN_PATH"
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
    if ! "$BIN_PATH" --version >/dev/null 2>&1; then
        die "installation verification failed"
    fi
    info "Installation successful!"
    info ""
    info "wiki version:"
    "$BIN_PATH" --version || true
}

main() {
    check_curl
    ensure_local_bin
    install_repo
    create_symlink

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
