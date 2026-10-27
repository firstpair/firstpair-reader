#!/bin/sh
# Install plugins from this repository into a sample vault and enable them.
#
#   sh samples/build/install-plugins.sh samples/shelf
#   sh samples/build/install-plugins.sh samples/triptych firstpair-triptych
#
# Copies each plugin's release files (manifest.json, main.js, styles.css)
# into <vault>/.obsidian/plugins/<id>/ and adds the id to
# .obsidian/community-plugins.json.  With no plugin named, a vault holding a
# Triptych index gets firstpair-triptych, any other firstpair-reader.  Open
# the folder as a vault in Obsidian and trust its plugins when asked.
set -eu

here=$(cd "$(dirname "$0")" && pwd)
plugins="$here/../../plugins"
vault=${1:?usage: install-plugins.sh <sample vault> [plugin id ...]}
shift
if [ $# -eq 0 ]; then
  if ls "$vault"/*/_data/triptych-reader.json >/dev/null 2>&1; then
    set -- firstpair-triptych
  else
    set -- firstpair-reader
  fi
fi

for id in "$@"; do
  [ -f "$plugins/$id/main.js" ] || { echo "no plugin $id in $plugins" >&2; exit 1; }
  dest="$vault/.obsidian/plugins/$id"
  mkdir -p "$dest"
  cp "$plugins/$id/manifest.json" "$plugins/$id/main.js" "$plugins/$id/styles.css" "$dest/"
  echo "installed $id in $dest"
done

python3 - "$vault/.obsidian/community-plugins.json" "$@" <<'PY'
import json, sys
from pathlib import Path
path = Path(sys.argv[1])
enabled = json.loads(path.read_text()) if path.exists() else []
for plugin in sys.argv[2:]:
    if plugin not in enabled:
        enabled.append(plugin)
path.write_text(json.dumps(enabled, indent=2) + "\n")
PY
