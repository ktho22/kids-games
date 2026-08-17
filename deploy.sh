#!/usr/bin/env bash
# Publish every game in this folder to Netlify.
#
#   ./deploy.sh          → publish live
#   ./deploy.sh preview  → private preview URL, live site untouched
#
# First run only: ./deploy.sh login   (opens the browser to authorize)

set -euo pipefail
cd "$(dirname "$0")"

# Pinned to a major version that runs on current Node. Older lines such as
# netlify-cli@17 exit silently on Node 25, which looks like a login problem
# but is really the CLI failing to start.
NETLIFY="npx --yes netlify-cli@27"

require_cli() {
  if ! $NETLIFY --version >/dev/null 2>&1; then
    echo "❌ The Netlify command line tool could not start."
    echo "   Check your internet connection, then try again."
    echo "   (Node version here: $(node --version 2>/dev/null || echo 'not found'))"
    exit 1
  fi
}

case "${1:-prod}" in
  login)
    require_cli
    echo "🔑 Opening the browser so you can authorize Netlify…"
    $NETLIFY login
    echo "✅ Done. Now run: ./deploy.sh"
    ;;
  preview)
    require_cli
    echo "👀 Uploading a private preview…"
    $NETLIFY deploy --dir=.
    ;;
  prod)
    require_cli
    # `netlify status` exits 0 even when logged out, so read what it says.
    if $NETLIFY status 2>&1 | grep -q "Not logged in"; then
      echo "❌ Not signed in to Netlify yet."
      echo "   Run this first:  ./deploy.sh login"
      exit 1
    fi
    echo "🚀 Publishing the games…"
    $NETLIFY deploy --prod --dir=.
    echo "✅ Live! Share the URL above with the kids."
    ;;
  *)
    echo "Usage: ./deploy.sh [login|preview|prod]"
    exit 1
    ;;
esac
