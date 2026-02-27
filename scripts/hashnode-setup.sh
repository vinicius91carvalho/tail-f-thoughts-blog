#!/usr/bin/env bash
#
# hashnode-setup.sh — Validate Hashnode credentials and update publication settings
#
# Usage: bash scripts/hashnode-setup.sh
#
# Requires: .env file with HASHNODE_PAT and HASHNODE_PUBLICATION_ID

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check dependencies
if ! command -v curl &> /dev/null; then
    log_error "curl is required but not installed."
    exit 1
fi

if ! command -v jq &> /dev/null; then
    log_warn "jq is not installed. Output will be raw JSON."
    HAS_JQ=false
else
    HAS_JQ=true
fi

# Load .env
if [ ! -f "$ENV_FILE" ]; then
    log_error ".env file not found at $ENV_FILE"
    log_info "Copy .env.example to .env and fill in your credentials:"
    log_info "  cp .env.example .env"
    exit 1
fi

set -a
source "$ENV_FILE"
set +a

# Validate required vars
if [ -z "${HASHNODE_PAT:-}" ] || [ "$HASHNODE_PAT" = "your_personal_access_token_here" ]; then
    log_error "HASHNODE_PAT is not set or still has the placeholder value."
    exit 1
fi

if [ -z "${HASHNODE_PUBLICATION_ID:-}" ] || [ "$HASHNODE_PUBLICATION_ID" = "your_publication_id_here" ]; then
    log_error "HASHNODE_PUBLICATION_ID is not set or still has the placeholder value."
    exit 1
fi

HASHNODE_API="https://gql.hashnode.com"

# --- Step 1: Validate token by fetching current user ---
log_info "Validating API token..."

ME_QUERY='{"query":"{ me { id username name } }"}'

ME_RESPONSE=$(curl -s -X POST "$HASHNODE_API" \
    -H "Content-Type: application/json" \
    -H "Authorization: $HASHNODE_PAT" \
    -d "$ME_QUERY")

if echo "$ME_RESPONSE" | grep -q '"errors"'; then
    log_error "API token is invalid or expired."
    if [ "$HAS_JQ" = true ]; then
        echo "$ME_RESPONSE" | jq '.errors'
    else
        echo "$ME_RESPONSE"
    fi
    exit 1
fi

if [ "$HAS_JQ" = true ]; then
    USERNAME=$(echo "$ME_RESPONSE" | jq -r '.data.me.username')
    FULLNAME=$(echo "$ME_RESPONSE" | jq -r '.data.me.name')
    log_info "Authenticated as: $FULLNAME (@$USERNAME)"
else
    log_info "Authentication successful."
    echo "$ME_RESPONSE"
fi

# --- Step 2: Fetch publication info ---
log_info "Fetching publication info..."

PUB_QUERY=$(cat <<EOF
{"query":"{ publication(id: \"$HASHNODE_PUBLICATION_ID\") { id title url about { text } } }"}
EOF
)

PUB_RESPONSE=$(curl -s -X POST "$HASHNODE_API" \
    -H "Content-Type: application/json" \
    -H "Authorization: $HASHNODE_PAT" \
    -d "$PUB_QUERY")

if echo "$PUB_RESPONSE" | grep -q '"errors"'; then
    log_error "Could not fetch publication. Check your HASHNODE_PUBLICATION_ID."
    if [ "$HAS_JQ" = true ]; then
        echo "$PUB_RESPONSE" | jq '.errors'
    else
        echo "$PUB_RESPONSE"
    fi
    exit 1
fi

if [ "$HAS_JQ" = true ]; then
    PUB_TITLE=$(echo "$PUB_RESPONSE" | jq -r '.data.publication.title')
    PUB_URL=$(echo "$PUB_RESPONSE" | jq -r '.data.publication.url')
    log_info "Publication: $PUB_TITLE"
    log_info "URL: $PUB_URL"
else
    log_info "Publication found."
    echo "$PUB_RESPONSE"
fi

# --- Step 3: Publication settings reminder ---
# Note: Hashnode's public GraphQL API does not expose mutations to update
# publication title, about, or SEO description. These must be set manually
# via the Hashnode dashboard.

echo ""
log_info "Publication settings to configure manually at:"
echo "  https://hashnode.com/${USERNAME:-your-username}/dashboard/appearance"
echo ""
echo "  Title: tail -f thoughts"
echo "  SEO Description: Blog sobre engenharia de software, liderança técnica"
echo "    e arquitetura. Experiências reais, erros honestos e aprendizados práticos."
echo "  About/Bio: Engineering Manager na Pagaleve, São Paulo. Desenvolvedor"
echo "    full-cycle apaixonado por JS/TS, React, Node, AWS e arquitetura limpa."
echo "    AWS Certified Cloud Practitioner. Compartilho aqui o que aprendo,"
echo "    o que deu errado e o que valeu a pena."

# --- Summary ---
echo ""
echo "=========================================="
echo "  Setup complete!"
echo "=========================================="
echo ""
log_info "Next steps (manual):"
echo "  1. Go to https://hashnode.com/settings"
echo "  2. Navigate to your publication dashboard"
echo "  3. Go to 'Integrations' > 'GitHub'"
echo "  4. Install the Hashnode GitHub App"
echo "  5. Select this repository and the 'articles/published' directory"
echo "  6. Commits to articles/published/ will auto-publish"
echo ""
log_info "To create your first post, run: /blog-post"
