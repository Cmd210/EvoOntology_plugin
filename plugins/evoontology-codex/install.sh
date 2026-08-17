#!/usr/bin/env sh
set -eu

plugin_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
skills_root="${CODEX_SKILLS_HOME:-$HOME/.agents/skills}"
mkdir -p "$skills_root"
cp -R "$plugin_root/skills/." "$skills_root/"
printf 'Installed EvoOntology skills to %s\n' "$skills_root"
