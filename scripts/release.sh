#!/bin/sh
# Check that the bundles are current and the tests pass, then list, for each
# plugin, the files a vault installs under .obsidian/plugins/<id>/.
set -eu
cd "$(dirname "$0")/.."
npm test --silent
for plugin in firstpair-reader firstpair-triptych; do
  version=$(node -p "require('./plugins/$plugin/manifest.json').version")
  echo "$plugin $version -> .obsidian/plugins/$plugin/"
  for file in manifest.json main.js styles.css; do
    sum=$(node -e "process.stdout.write(require('crypto').createHash('sha256').update(require('fs').readFileSync(process.argv[1])).digest('hex'))" "plugins/$plugin/$file")
    echo "  plugins/$plugin/$file  sha256 $sum"
  done
done
