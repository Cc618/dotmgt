#!/bin/sh

set -e

cd "$(dirname "$0")/test"

bin="$(realpath ../src/txtpp.py)"

fail=0
for input in txtpp.*; do
    target="${input#"txtpp."}"

    echo "* $input"

    # If error
    if ! "$bin" "$input" > /tmp/txtpp.test; then
        echo "Got exit code $?" >&2
        echo >&2
        fail=1
    elif ! diff --color "$target" /tmp/txtpp.test; then
        fail=1
        echo "----------------" >&2
        echo >&2
    fi
done

if [ "$fail" != 0 ]; then
    echo Test failed >&2
else
    echo Test OK
fi

exit "$fail"
