#!/bin/sh
# Run a command in the xc7 environment, the nextpnr checkout this script is
# in mounted at /src, as you: `xc7/run.sh make -f xc7/Makefile`, or no
# command for a shell. The image is built from xc7/Containerfile first,
# which takes no time once it is.
set -e
here=$(cd "$(dirname "$0")/.." && pwd)
image=localhost/nextpnr-xc7
podman build -q -t "$image" "$here/xc7" >/dev/null
[ $# -eq 0 ] && set -- bash
tty=""
[ -t 0 ] && tty="-it"
exec podman run --rm $tty --userns=keep-id -v "$here:/src" -w /src "$image" "$@"
