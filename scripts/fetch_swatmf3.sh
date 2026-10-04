#!/usr/bin/env bash
# Download the Linux SWAT-MODFLOW3 program from its GitHub release and put it where the
# plugin copies it from, as `swatmf3`, in both folders that every new project gets:
#   src/qswatmod/FOLDER_FOR_COPY/SWAT-MODFLOW/   and   .../SM_exes/
#
#   scripts/fetch_swatmf3.sh              # version in swatmf3-version.txt
#   scripts/fetch_swatmf3.sh v1.2.5       # another release
#   SWATMF3_ASSET=ifx-lin_x86_64 scripts/fetch_swatmf3.sh   # Intel ifx build instead of gfortran
#
# The binary is not committed (see src/qswatmod/.gitignore).
set -euo pipefail

repo="spark-hydro/SWAT-MODFLOW3"
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
version="${1:-$(tr -d '[:space:]' < "$root/swatmf3-version.txt")}"
asset="${SWATMF3_ASSET:-gnu-lin_x86_64}"
zip="swatmf3-${version}-${asset}-Rel.zip"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

echo "Downloading $zip from $repo"
if command -v gh >/dev/null 2>&1; then
    gh release download "$version" --repo "$repo" --pattern "$zip" --dir "$tmp"
else
    curl -fsSL -o "$tmp/$zip" "https://github.com/$repo/releases/download/$version/$zip"
fi

python3 -m zipfile -e "$tmp/$zip" "$tmp/x"
exe="$(find "$tmp/x" -type f -name 'swatmf3-*' | head -1)"
[ -n "$exe" ] || { echo "no swatmf3-* program in $zip" >&2; exit 1; }
chmod +x "$exe"

for d in SWAT-MODFLOW SM_exes; do
    dest="$root/src/qswatmod/FOLDER_FOR_COPY/$d"
    mkdir -p "$dest"
    cp "$exe" "$dest/swatmf3"
done
echo "Installed swatmf3 ($version, $asset) in FOLDER_FOR_COPY/SWAT-MODFLOW and SM_exes"
"$root/src/qswatmod/FOLDER_FOR_COPY/SWAT-MODFLOW/swatmf3" --version | sed -n '/SWAT-MODFLOW3/,$p'
