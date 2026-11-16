#!/usr/bin/env bash
# Run the defensive-core resistance suite in an isolated interpreter (-I). No network, no config
# bleed: the test sets CTF_FLAG / WORK_DIR / SUBMIT_* itself, so it never reads the live .flagfmt.
set -euo pipefail
here="$(cd "$(dirname "$0")/../.." && pwd)"
py="$here/.venv/bin/python"
[ -x "$py" ] || py="python3"
exec "$py" -I "$here/tests/injection/test_injection.py"
