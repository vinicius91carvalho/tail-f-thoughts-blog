---
name: hashnode
description: Manage the Hashnode blog via API — publish posts, manage drafts, series, tags, comments, webhooks, and redirects. Use when the user needs to interact with the Hashnode API directly.
argument-hint: "[command] (e.g., 'post publish', 'tag get javascript', 'pub info')"
---

# /hashnode — Hashnode API Management Skill

Manage the "tail -f thoughts" Hashnode blog via `scripts/hashnode-api.py`.
All commands output JSON. The tool reads `.env` for `HASHNODE_PAT` and `HASHNODE_PUBLICATION_ID`.

User argument: $ARGUMENTS

## Quick Reference

| Task | Command |
|------|---------|
| **Publish a post** | `python3 scripts/hashnode-api.py post publish <file.md>` |
| **Update a post** | `python3 scripts/hashnode-api.py post update <id> [opts]` |
| **Get post by slug** | `python3 scripts/hashnode-api.py post get <slug>` |
| **List posts** | `python3 scripts/hashnode-api.py post list` |
| **Remove a post** | `python3 scripts/hashnode-api.py post remove <id>` |
| **Create draft** | `python3 scripts/hashnode-api.py draft create <file.md>` |
| **Publish draft** | `python3 scripts/hashnode-api.py draft publish <draft-id>` |
| **Schedule draft** | `python3 scripts/hashnode-api.py draft schedule <id> <datetime>` |
| **List drafts** | `python3 scripts/hashnode-api.py draft list` |
| **List series** | `python3 scripts/hashnode-api.py series list` |
| **Add post to series** | `python3 scripts/hashnode-api.py series add-post <post-id> <series-id>` |
| **Look up a tag** | `python3 scripts/hashnode-api.py tag get <slug>` |
| **Search tags** | `python3 scripts/hashnode-api.py tag search <query>` |
| **List comments** | `python3 scripts/hashnode-api.py comment list <post-id-or-slug>` |
| **Publication info** | `python3 scripts/hashnode-api.py pub info` |
| **Auth check** | `python3 scripts/hashnode-api.py pub me` |
| **Blog stats** | `python3 scripts/hashnode-api.py pub stats` |
| **List webhooks** | `python3 scripts/hashnode-api.py webhook list` |
| **List redirects** | `python3 scripts/hashnode-api.py redirect list` |

## Publishing Workflow

When publishing a post from a markdown file in `articles/published/`:

1. **Resolve tags first**: Run `tag get <slug>` for each tag to verify they exist on Hashnode
2. **Publish**: `post publish <file.md> [--series <id>] [--delisted]`
   - The tool auto-resolves tag slugs from frontmatter to `{id, name, slug}` objects
   - Automatically sets SEO metaTags (title with ` | tail -f thoughts` suffix)
   - Enables TOC and slugOverridden by default
3. **Apply update settings**: `post update <id> --pin --enable-comments`
   - Field names differ between publishPost and updatePost mutations
   - The tool handles this automatically

### Example: Full publish flow

```bash
# 1. Check tags exist
python3 scripts/hashnode-api.py tag get artificial-intelligence
python3 scripts/hashnode-api.py tag get opinion

# 2. Publish from file
python3 scripts/hashnode-api.py post publish articles/published/my-post.md \
  --series 69a59f7c1c85a3885e262882

# 3. Pin to blog and confirm settings
python3 scripts/hashnode-api.py post update <returned-id> --pin --enable-comments
```

## Post Management

### Update post content
```bash
python3 scripts/hashnode-api.py post update <id> --content-file articles/published/my-post.md
```

### Update SEO metadata
```bash
python3 scripts/hashnode-api.py post update <id> \
  --meta-title "New Title | tail -f thoughts" \
  --meta-description "Compelling description under 160 chars"
```

### Pin/unpin a post
```bash
python3 scripts/hashnode-api.py post update <id> --pin
python3 scripts/hashnode-api.py post update <id> --no-pin
```

### Delist from community feed (opinion/non-tech posts)
```bash
python3 scripts/hashnode-api.py post update <id> --delisted
```

## Draft Workflow

```bash
# Create draft from file
python3 scripts/hashnode-api.py draft create articles/drafts/my-draft.md

# Schedule for future
python3 scripts/hashnode-api.py draft schedule <draft-id> 2026-03-15T10:00:00Z

# Or publish immediately
python3 scripts/hashnode-api.py draft publish <draft-id>

# Cancel schedule
python3 scripts/hashnode-api.py draft cancel-schedule <scheduled-post-id>
```

## Series Management

Known series IDs (from MEMORY.md):
- **Thoughts**: `69a59f7c1c85a3885e262882`
- **Vibe Coding Engineering**: `69a59f7d1c85a3885e262883`
- **Building in Public**: `69a59f8ce526d8cf7ef8b308`

```bash
# List all series
python3 scripts/hashnode-api.py series list

# Assign post to series at publish time
python3 scripts/hashnode-api.py post publish file.md --series 69a59f7c1c85a3885e262882

# Add existing post to series
python3 scripts/hashnode-api.py series add-post <post-id> <series-id>
```

## Safety Rules

1. **Never delete and republish** — triggers AutoMod spam detection. Use `post update` instead
2. **Always include full settings** — SEO metaTags, TOC, tags with real IDs (the tool does this automatically)
3. **Non-technical posts**: use `--delisted` flag to hide from Hashnode community feed
4. **Slugs are permanent** — even deleted posts keep their slug. Choose carefully
5. **Verify tags exist** before publishing — use `tag get <slug>` to confirm
6. **Markdown links in series descriptions** may cause 400 errors — use plain text

## Integration with /blog-post

In Phase 4 (Finalize) of the `/blog-post` workflow, use this skill to publish:

1. `/blog-post` prepares the file in `articles/published/`
2. Use `/hashnode post publish articles/published/<slug>.md --series <id>` to publish via API
3. Use `/hashnode post update <id> --pin` to apply post-publish settings

## JSON Output Format

All commands return structured JSON:

```json
// Success
{"ok": true, "data": {...}, "message": "Post published: https://..."}

// Error
{"ok": false, "error": "Tag not found: nonexistent", "details": {...}}
```

Parse with `jq` or read directly from Claude Code tool output.
