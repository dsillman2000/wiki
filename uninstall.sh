#!/bin/sh
set -e

BIN_DIR="$HOME/.local/bin"
BIN_PATH="$BIN_DIR/wiki"
INSTALL_DIR="$HOME/.local/share/wiki-client"

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

uninstall_package() {
    if python3 -m pip show wiki-client >/dev/null 2>&1; then
        python3 -m pip uninstall --yes wiki-client
        printf 'Uninstalled wiki-client Python package\n'
    fi
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

    if ! command -v wiki >/dev/null 2>&1 && [ ! -e "$BIN_PATH" ]; then
        printf 'wiki is not installed\n'
        exit 0
    fi

    if [ $yes_flag -eq 0 ]; then
        confirm "Uninstall wiki-client?" || {
            printf 'cancelled\n'
            exit 0
        }
    fi

    uninstall_package

    if [ $remove_repo -eq 1 ]; then
        remove_install_dir
    fi

    remove_empty_bin_dir
    printf 'Uninstallation complete\n'
}

main "$@"
