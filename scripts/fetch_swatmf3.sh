#!/usr/bin/env bash
# Download the SWAT-MODFLOW3 program from its GitHub release and put it where the plugin
# copies it from (the folder every new project gets and the Run button uses):
#   src/qswatmod/FOLDER_FOR_COPY/SWAT-MODFLOW/swatmf3       (Linux, gfortran, static)
#   src/qswatmod/FOLDER_FOR_COPY/SWAT-MODFLOW/swatmf3.exe   (Windows, gfortran)
#
#   scripts/fetch_swatmf3.sh                    # Linux program, version in swatmf3-version.txt
#   scripts/fetch_swatmf3.sh v1.2.5             # another release
#   SWATMF3_PLATFORM=windows scripts/fetch_swatmf3.sh   # Windows program only
#   SWATMF3_PLATFORM=all scripts/fetch_swatmf3.sh       # both (what the release workflow uses)
#   SWATMF3_ASSET=ifx-lin_x86_64 scripts/fetch_swatmf3.sh   # Intel ifx build for Linux instead
#
# The programs are not committed (see src/qswatmod/.gitignore).
set -euo pipefail

repo="spark-hydro/SWAT-MODFLOW3"
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
version="${1:-$(tr -d '[:space:]' < "$root/swatmf3-version.txt")}"
platform="${SWATMF3_PLATFORM:-linux}"
dest="$root/src/qswatmod/FOLDER_FOR_COPY/SWAT-MODFLOW"

case "$platform" in linux|windows|all) ;; *) echo "SWATMF3_PLATFORM must be linux, windows or all" >&2; exit 1 ;; esac

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
mkdir -p "$dest"

fetch_asset() {  # fetch_asset ASSET TARGET_NAME
    local asset="$1" target="$2" zip="swatmf3-${version}-$1-Rel.zip"
    echo "Downloading $zip from $repo"
    if command -v gh >/dev/null 2>&1; then
        gh release download "$version" --repo "$repo" --pattern "$zip" --dir "$tmp"
    else
        curl -fsSL -o "$tmp/$zip" "https://github.com/$repo/releases/download/$version/$zip"
    fi
    rm -rf "$tmp/x"
    python3 -m zipfile -e "$tmp/$zip" "$tmp/x"
    local exe
    exe="$(find "$tmp/x" -type f -name 'swatmf3-*' | head -1)"
    [ -n "$exe" ] || { echo "no swatmf3-* program in $zip" >&2; exit 1; }
    cp "$exe" "$dest/$target"
    chmod +x "$dest/$target"
    echo "Installed $target ($version, $asset) in FOLDER_FOR_COPY/SWAT-MODFLOW"
}

if [ "$platform" = linux ] || [ "$platform" = all ]; then
    fetch_asset "${SWATMF3_ASSET:-gnu-lin_x86_64}" swatmf3
    "$dest/swatmf3" --version | sed -n '/SWAT-MODFLOW3/,$p'
fi
if [ "$platform" = windows ] || [ "$platform" = all ]; then
    fetch_asset gnu-win_amd64 swatmf3.exe
fi
