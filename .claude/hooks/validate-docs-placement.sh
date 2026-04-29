#!/usr/bin/env bash
# validate-docs-placement.sh — Warns when staged documentation contains
# internal markers that should not appear in the public repository.
#
# This is an awareness hook, not a blocker. Warnings go to stderr.
#
# Rule: "Would a hiring manager see this as expertise or learning in progress?"
# If not, move the content to docs/internal/ (gitignored).

set -euo pipefail

# Only check staged markdown files in docs/ (excluding docs/internal/, which is
# gitignored and intended for working notes).
STAGED_DOCS=$(git diff --cached --name-only --diff-filter=ACM -- 'docs/*.md' 'docs/**/*.md' 2>/dev/null \
    | grep -v '^docs/internal/' \
    || true)

if [ -z "$STAGED_DOCS" ]; then
    exit 0
fi

WARNINGS=0

for file in $STAGED_DOCS; do
    MARKERS=""

    # Check for internal-marker section headers.
    if grep -qiE '^\s*#+\s*(open questions|todo|practice exercises|training rubric|gap analysis|session notes)' "$file" 2>/dev/null; then
        MARKERS="section headers with internal markers"
    fi

    # Check for inline TODO items.
    if grep -qiE '\bTODO\b.*:' "$file" 2>/dev/null; then
        MARKERS="${MARKERS:+$MARKERS, }TODO items"
    fi

    # Check for competency checkpoint markers.
    if grep -qiE '^\s*#+\s*.*competency checkpoint' "$file" 2>/dev/null; then
        MARKERS="${MARKERS:+$MARKERS, }competency checkpoints"
    fi

    if [ -n "$MARKERS" ]; then
        echo "warning: docs-placement: $file contains $MARKERS" >&2
        echo "  Consider moving to docs/internal/ (see docs/superpowers/specs/ for the public-vs-internal rule)." >&2
        WARNINGS=$((WARNINGS + 1))
    fi
done

if [ "$WARNINGS" -gt 0 ]; then
    echo "" >&2
    echo "$WARNINGS file(s) may belong in docs/internal/ instead of public docs/." >&2
    echo "Rule: 'Would a hiring manager see this as expertise or learning in progress?'" >&2
fi

exit 0
