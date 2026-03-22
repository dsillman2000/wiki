#!/bin/sh
set -e

BIN_DIR="$HOME/.local/bin"
BIN_PATH="$BIN_DIR/wiki"
INSTALL_DIR="$HOME/.local/share/wiki-cli"

confirm() {
    printf '%s ' "$*" >&2
    printf '[y/N] ' >&2
    read -r answer || answer=""
    case "$answer" in
        [yY]|[yY][eE][sS])
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

remove_binary() {
    if [ -L "$BIN_PATH" ]; then
        rm "$BIN_PATH"
        return 0
    elif [ -e "$BIN_PATH" ]; then
        printf 'error: %s exists but is not a symlink\n' "$BIN_PATH" >&2
        return 1
    fi
    return 0
}

remove_install_dir() {
    if [ -d "$INSTALL_DIR" ]; then
        confirm "Remove $INSTALL_DIR directory?" || return 0
        rm -rf "$INSTALL_DIR"
        printf 'Removed %s\n' "$INSTALL_DIR"
    fi
}

remove_empty_bin_dir() {
    if [ -d "$BIN_DIR" ]; then
        if [ -z "$(ls -A "$BIN_DIR" 2>/dev/null)" ]; then
            rmdir "$BIN_DIR"
            printf 'Removed empty directory %s\n' "$BIN_DIR"
        fi
    fi
}

main() {
    yes_flag=0
    remove_repo=0

    while [ $# -gt 0 ]; do
        case "$1" in
            --yes|-y)
                yes_flag=1
                ;;
            --remove-repo)
                remove_repo=1
                ;;
            *)
                printf 'usage: %s [--yes] [--remove-repo]\n' "$0" >&2
                exit 1
                ;;
        esac
        shift
    done

    if [ ! -L "$BIN_PATH" ] && [ ! -e "$BIN_PATH" ]; then
        printf 'wiki is not installed\n'
        exit 0
    fi

    if [ $yes_flag -eq 0 ]; then
        confirm "Remove wiki from $BIN_PATH?" || {
            printf 'cancelled\n'
            exit 0
        }
    fi

    remove_binary && printf 'Removed %s\n' "$BIN_PATH"

    if [ $remove_repo -eq 1 ]; then
        remove_install_dir
    fi

    remove_empty_bin_dir
    printf 'Uninstallation complete\n'
}

main "$@"
