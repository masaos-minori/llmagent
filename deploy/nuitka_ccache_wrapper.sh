#!/bin/bash
# nuitka_ccache_wrapper.sh
# Stand-in for ccache, selected through NUITKA_CCACHE_BINARY by build_binaries.sh.
# Nuitka runs it as `<this script> <C compiler> <arguments...>`.
#
# Nuitka writes a per-binary __helpers.h into each build directory and every module
# C file includes it, so identical third-party modules preprocess differently in
# different binaries and ccache never hits across them. Before delegating to the real
# ccache, replace that header with the canonical superset from
# tools/gen_nuitka_helpers_header.py (NUITKA_CANON_HELPERS). The replacement is atomic
# because parallel compiler processes of one build call this wrapper concurrently.
#
# Environment:
#   NUITKA_CANON_HELPERS  canonical header; unset or missing means plain pass-through
#   NUITKA_REAL_CCACHE    ccache executable to delegate to (default: ccache in PATH)

set -u

canon="${NUITKA_CANON_HELPERS:-}"
real_ccache="${NUITKA_REAL_CCACHE:-ccache}"

if [[ -n "${canon}" && -f "${canon}" ]]; then
    for arg in "$@" .; do
        case "${arg}" in
            -I*) dir="${arg#-I}" ;;
            *.c) dir="$(dirname -- "${arg}")" ;;
            .) dir="." ;;
            *) continue ;;
        esac
        header="${dir}/__helpers.h"
        if [[ -f "${header}" ]] && ! cmp -s -- "${canon}" "${header}"; then
            tmp="${header}.canon.$$"
            if cp -- "${canon}" "${tmp}"; then
                mv -f -- "${tmp}" "${header}" || rm -f -- "${tmp}"
            fi
        fi
    done
fi

exec "${real_ccache}" "$@"
