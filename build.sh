#!/bin/sh
set -e
cd "$(dirname "$0")"
.venv/bin/python build.py
npx esbuild src/editor.js --bundle --format=esm --minify --outfile=public/editor.js --log-level=warning
node scripts/build-sw.mjs
