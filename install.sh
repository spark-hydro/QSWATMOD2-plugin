#!/usr/bin/env bash
# Install the QSWATMOD2 plugin into a QGIS profile (tested on Linux with conda QGIS 3.44;
# the Flatpak and macOS folders are untested).
#
#   curl -fsSL https://raw.githubusercontent.com/spark-hydro/QSWATMOD2-plugin/main/install.sh | bash
#   ./install.sh                       # latest release, Linux ZIP (SWAT-MODFLOW3 for Linux inside)
#   ./install.sh --version v2.11.0     # a specific release
#   ./install.sh --full                # the ZIP with the Windows programs too (16 MB)
#   ./install.sh --zip QSWATMOD2.2.11.0-linux.zip     # a ZIP you already have
#   ./install.sh --flatpak             # QGIS installed from Flatpak
#   ./install.sh --profile work        # another QGIS profile (default: default)
#   ./install.sh --plugins-dir DIR     # any plugins folder
#   ./install.sh --uninstall
#
# Then restart QGIS and tick QSWATMOD2 in Plugins > Manage and Install Plugins > Installed.
# QGIS 3 only: the plugin is not ported to QGIS 4 (Qt6) yet.
set -euo pipefail

repo="spark-hydro/QSWATMOD2-plugin"
name="QSWATMOD2"
version=""; zip=""; url=""; profile="default"; flatpak=0; full=0; uninstall=0; force=0
plugins_dir="${QGIS_PLUGINS_DIR:-}"

usage() { sed -n '2,16p' "$0" | sed 's/^# \{0,1\}//'; }
die() { echo "install.sh: $*" >&2; exit 1; }

while [ $# -gt 0 ]; do
    case "$1" in
        --version)     version="${2:?--version needs a value}"; shift 2 ;;
        --zip)         zip="${2:?--zip needs a file}"; shift 2 ;;
        --url)         url="${2:?--url needs a URL}"; shift 2 ;;
        --profile)     profile="${2:?--profile needs a name}"; shift 2 ;;
        --plugins-dir) plugins_dir="${2:?--plugins-dir needs a folder}"; shift 2 ;;
        --flatpak)     flatpak=1; shift ;;
        --full)        full=1; shift ;;
        --uninstall)   uninstall=1; shift ;;
        --force)       force=1; shift ;;
        -h|--help)     usage; exit 0 ;;
        *)             die "unknown option $1 (see --help)" ;;
    esac
done

if [ -z "$plugins_dir" ]; then
    if [ "$flatpak" = 1 ]; then
        base="$HOME/.var/app/org.qgis.qgis/data/QGIS/QGIS3"
    elif [ "$(uname -s)" = Darwin ]; then
        base="$HOME/Library/Application Support/QGIS/QGIS3"
    else
        base="${XDG_DATA_HOME:-$HOME/.local/share}/QGIS/QGIS3"
    fi
    plugins_dir="$base/profiles/$profile/python/plugins"
fi
target="$plugins_dir/$name"

if [ "$uninstall" = 1 ]; then
    [ -e "$target" ] || [ -L "$target" ] || die "nothing to remove: $target does not exist"
    if [ -L "$target" ] && [ "$force" = 0 ]; then
        die "$target is a symbolic link (a development install); use --force to remove the link"
    fi
    rm -rf "$target"
    echo "Removed $target"
    exit 0
fi

fetch() {  # fetch URL FILE
    if command -v curl >/dev/null 2>&1; then curl -fsSL -o "$2" "$1"
    elif command -v wget >/dev/null 2>&1; then wget -q -O "$2" "$1"
    else die "need curl or wget"; fi
}

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

if [ -z "$zip" ]; then
    suffix="-linux"; [ "$full" = 1 ] && suffix=""
    if [ -z "$url" ]; then
        if [ -z "$version" ]; then
            echo "Looking for the latest release of $repo"
            fetch "https://api.github.com/repos/$repo/releases/latest" "$tmp/release.json"
            version="$(sed -n 's/.*"tag_name": *"\([^"]*\)".*/\1/p' "$tmp/release.json" | head -1)"
            [ -n "$version" ] || die "could not find the latest release"
        fi
        case "$version" in v*) ;; *) version="v$version" ;; esac
        file="$name.${version#v}$suffix.zip"
        url="https://github.com/$repo/releases/download/$version/$file"
    else
        file="$(basename "${url%%\?*}")"
    fi
    echo "Downloading $url"
    fetch "$url" "$tmp/$file" || die "download failed (is $version a release with $file?)"
    # verify with SHA256SUMS when the release has one
    if fetch "${url%/*}/SHA256SUMS" "$tmp/SHA256SUMS" 2>/dev/null; then
        (cd "$tmp" && grep " $file\$" SHA256SUMS | sha256sum -c -) || die "checksum does not match"
    else
        echo "No SHA256SUMS next to the file: not verified"
    fi
    zip="$tmp/$file"
fi
[ -f "$zip" ] || die "$zip not found"

# the ZIP must hold one folder, QSWATMOD2/, with metadata.txt inside
python3 - "$zip" "$name" <<'PY' || exit 1
import sys, zipfile
z, name = sys.argv[1:]
names = zipfile.ZipFile(z).namelist()
tops = {n.split("/")[0] for n in names}
if tops != {name} or name + "/metadata.txt" not in names:
    sys.exit("install.sh: %s is not a %s plugin ZIP (top-level: %s)" % (z, name, sorted(tops)[:3]))
PY

if [ -L "$target" ] && [ "$force" = 0 ]; then
    die "$target is a symbolic link (a development install); use --force to replace it"
fi
mkdir -p "$plugins_dir"
python3 -m zipfile -e "$zip" "$tmp/unzipped"
rm -rf "$target"
mv "$tmp/unzipped/$name" "$target"
# unzip drops the execute bit; the plugin also sets it when it runs the model
find "$target/FOLDER_FOR_COPY" -type f \( -name 'swatmf3' -o -name 'swatmf3-*' \) -exec chmod +x {} + 2>/dev/null || true

ver="$(sed -n 's/^version=//p' "$target/metadata.txt" | head -1 | tr -d '\r')"
echo "Installed $name $ver in $target"
echo "Restart QGIS, then tick $name in Plugins > Manage and Install Plugins > Installed."
