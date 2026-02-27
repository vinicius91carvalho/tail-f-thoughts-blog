#!/usr/bin/env bash
#
# publish.sh — Publish a markdown article to Hashnode via GraphQL API
#
# Usage: bash scripts/publish.sh <path-to-article.md>
#
# Requires: .env file with HASHNODE_PAT and HASHNODE_PUBLICATION_ID

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

if [ $# -lt 1 ]; then
    log_error "Usage: bash scripts/publish.sh <path-to-article.md>"
    exit 1
fi

ARTICLE_PATH="$1"

if [ ! -f "$ARTICLE_PATH" ]; then
    log_error "File not found: $ARTICLE_PATH"
    exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
    log_error ".env file not found. Copy .env.example to .env and fill in credentials."
    exit 1
fi

set -a
source "$ENV_FILE"
set +a

if [ -z "${HASHNODE_PAT:-}" ] || [ "$HASHNODE_PAT" = "your_personal_access_token_here" ]; then
    log_error "HASHNODE_PAT is not configured."
    exit 1
fi

if [ -z "${HASHNODE_PUBLICATION_ID:-}" ] || [ "$HASHNODE_PUBLICATION_ID" = "your_publication_id_here" ]; then
    log_error "HASHNODE_PUBLICATION_ID is not configured."
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    log_error "python3 is required."
    exit 1
fi

log_info "Publishing: $ARTICLE_PATH"

RESPONSE=$(python3 - "$ARTICLE_PATH" "$HASHNODE_PUBLICATION_ID" "$HASHNODE_PAT" << 'PYEOF'
import sys, json, urllib.request, re

article_path = sys.argv[1]
publication_id = sys.argv[2]
token = sys.argv[3]

with open(article_path, 'r') as f:
    content = f.read()

# Parse frontmatter
parts = content.split('---', 2)
if len(parts) < 3:
    print(json.dumps({"error": "Invalid frontmatter"}))
    sys.exit(1)

frontmatter = {}
for line in parts[1].strip().split('\n'):
    if ':' in line:
        key, val = line.split(':', 1)
        frontmatter[key.strip()] = val.strip().strip('"').strip("'")

markdown = parts[2].strip()

title = frontmatter.get('title', '')
subtitle = frontmatter.get('subtitle', '')
slug = frontmatter.get('slug', '')
tags_str = frontmatter.get('tags', '')

if not title:
    print(json.dumps({"error": "Missing title in frontmatter"}))
    sys.exit(1)

tags = []
for t in tags_str.split(','):
    t = t.strip()
    if t:
        tags.append({"slug": t, "name": t.replace('-', ' ').title()})

inp = {
    "title": title,
    "slug": slug,
    "publicationId": publication_id,
    "contentMarkdown": markdown,
}
if subtitle:
    inp["subtitle"] = subtitle
if tags:
    inp["tags"] = tags

payload = {
    "query": """mutation PublishPost($input: PublishPostInput!) {
        publishPost(input: $input) {
            post { id title slug url }
        }
    }""",
    "variables": {"input": inp}
}

data = json.dumps(payload).encode('utf-8')
req = urllib.request.Request(
    'https://gql.hashnode.com',
    data=data,
    headers={
        'Content-Type': 'application/json',
        'Authorization': token
    }
)

resp = urllib.request.urlopen(req)
print(resp.read().decode('utf-8'))
PYEOF
)

if echo "$RESPONSE" | grep -q '"errors"'; then
    log_error "Failed to publish:"
    echo "$RESPONSE"
    exit 1
fi

URL=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.loads(sys.stdin.read())['data']['publishPost']['post']['url'])" 2>/dev/null || echo "")

if [ -n "$URL" ]; then
    log_info "Published successfully!"
    log_info "URL: $URL"
else
    log_warn "Response:"
    echo "$RESPONSE"
fi
