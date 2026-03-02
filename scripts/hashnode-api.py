#!/usr/bin/env python3
"""
hashnode-api.py — CLI tool to manage Hashnode blog via GraphQL API.

Stdlib-only (no pip deps). Reads .env for credentials.
All output is JSON for easy parsing by scripts and Claude Code.

Usage: python3 scripts/hashnode-api.py <group> <command> [args] [flags]
       python3 scripts/hashnode-api.py --help
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
ENV_FILE = PROJECT_ROOT / ".env"
API_URL = "https://gql.hashnode.com"
BLOG_DOMAIN = "tail-f-thoughts.hashnode.dev"
BLOG_TITLE_SUFFIX = " | tail -f thoughts"

# ---------------------------------------------------------------------------
# .env parser (no python-dotenv)
# ---------------------------------------------------------------------------

def load_env(path: Path) -> dict:
    """Parse a .env file into a dict. Handles quotes and comments."""
    env = {}
    if not path.exists():
        return env
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip()
            # Strip surrounding quotes
            if len(val) >= 2 and val[0] == val[-1] and val[0] in ('"', "'"):
                val = val[1:-1]
            env[key] = val
    return env


def get_credentials() -> tuple:
    """Return (pat, publication_id) from env vars or .env file."""
    env = load_env(ENV_FILE)
    pat = os.environ.get("HASHNODE_PAT") or env.get("HASHNODE_PAT", "")
    pub_id = os.environ.get("HASHNODE_PUBLICATION_ID") or env.get("HASHNODE_PUBLICATION_ID", "")
    if not pat or pat == "your_personal_access_token_here":
        fail("HASHNODE_PAT not configured. Set it in .env or as an environment variable.")
    if not pub_id or pub_id == "your_publication_id_here":
        fail("HASHNODE_PUBLICATION_ID not configured. Set it in .env or as an environment variable.")
    return pat, pub_id

# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def ok(data, message: str = ""):
    """Print success JSON and exit 0."""
    out = {"ok": True, "data": data}
    if message:
        out["message"] = message
    print(json.dumps(out, indent=2, ensure_ascii=False))
    sys.exit(0)


def fail(error: str, details=None):
    """Print error JSON and exit 1."""
    out = {"ok": False, "error": error}
    if details:
        out["details"] = details
    print(json.dumps(out, indent=2, ensure_ascii=False))
    sys.exit(1)

# ---------------------------------------------------------------------------
# GraphQL client
# ---------------------------------------------------------------------------

def graphql(query: str, variables: dict = None, pat: str = None) -> dict:
    """Execute a GraphQL request. Returns parsed response."""
    if pat is None:
        pat, _ = get_credentials()
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": pat,
        },
    )
    try:
        resp = urllib.request.urlopen(req)
        body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        try:
            error_json = json.loads(error_body)
        except (json.JSONDecodeError, ValueError):
            error_json = {"raw": error_body}
        fail(f"HTTP {e.code}: {e.reason}", error_json)
    except urllib.error.URLError as e:
        fail(f"Network error: {e.reason}")

    if "errors" in body:
        fail(body["errors"][0].get("message", "GraphQL error"), body["errors"])
    return body.get("data", {})

# ---------------------------------------------------------------------------
# Frontmatter parser
# ---------------------------------------------------------------------------

def parse_frontmatter(filepath: str) -> tuple:
    """Parse a markdown file with YAML frontmatter. Returns (frontmatter_dict, markdown_body)."""
    with open(filepath) as f:
        content = f.read()

    parts = content.split("---", 2)
    if len(parts) < 3:
        fail(f"Invalid frontmatter in {filepath}. Expected --- delimiters.")

    fm = {}
    for line in parts[1].strip().split("\n"):
        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            # Handle booleans
            if val.lower() == "true":
                val = True
            elif val.lower() == "false":
                val = False
            fm[key] = val

    body = parts[2].strip()
    return fm, body

# ---------------------------------------------------------------------------
# Tag resolver
# ---------------------------------------------------------------------------

_tag_cache = {}


def resolve_tag(slug: str, pat: str = None) -> dict:
    """Resolve a tag slug to {id, name, slug} via the Hashnode API."""
    slug = slug.strip().lower()
    if slug in _tag_cache:
        return _tag_cache[slug]

    query = """
    query TagBySlug($slug: String!) {
        tag(slug: $slug) {
            id
            name
            slug
        }
    }
    """
    data = graphql(query, {"slug": slug}, pat=pat)
    tag = data.get("tag")
    if not tag:
        return None
    result = {"id": tag["id"], "name": tag["name"], "slug": tag["slug"]}
    _tag_cache[slug] = result
    return result


def resolve_tags(tags_str: str, pat: str = None) -> list:
    """Resolve comma-separated tag slugs to a list of tag objects."""
    resolved = []
    for t in tags_str.split(","):
        t = t.strip()
        if not t:
            continue
        tag = resolve_tag(t, pat=pat)
        if tag:
            resolved.append(tag)
        else:
            print(json.dumps({"warning": f"Tag '{t}' not found on Hashnode, skipping"}),
                  file=sys.stderr)
    return resolved

# ---------------------------------------------------------------------------
# Settings builders
# ---------------------------------------------------------------------------

def build_publish_settings(delisted: bool = False, newsletter: bool = False) -> dict:
    """Build settings for publishPost mutation."""
    return {
        "enableTableOfContent": True,
        "slugOverridden": True,
        "delisted": delisted,
        "isNewsletterActivated": newsletter,
    }


def build_update_settings(
    pin: bool = None,
    delisted: bool = None,
    disable_comments: bool = None,
) -> dict:
    """Build settings for updatePost mutation."""
    settings = {"isTableOfContentEnabled": True}
    if pin is not None:
        settings["pinToBlog"] = pin
    if delisted is not None:
        settings["delisted"] = delisted
    if disable_comments is not None:
        settings["disableComments"] = disable_comments
    return settings


def build_draft_settings(delisted: bool = False, newsletter: bool = False) -> dict:
    """Build settings for createDraft mutation."""
    return {
        "enableTableOfContent": True,
        "slugOverridden": True,
        "delist": delisted,
        "activateNewsletter": newsletter,
    }


def build_meta_tags(title: str, description: str) -> dict:
    """Build SEO metaTags. Appends blog title suffix."""
    seo_title = title
    if BLOG_TITLE_SUFFIX not in seo_title:
        seo_title = seo_title[:60 - len(BLOG_TITLE_SUFFIX)] + BLOG_TITLE_SUFFIX
    return {
        "title": seo_title[:60],
        "description": description[:160],
    }

# ---------------------------------------------------------------------------
# POST commands
# ---------------------------------------------------------------------------

def cmd_post_publish(args):
    """Publish a post from a markdown file."""
    pat, pub_id = get_credentials()
    fm, body = parse_frontmatter(args.file)

    title = fm.get("title", "")
    if not title:
        fail("Missing 'title' in frontmatter")
    subtitle = fm.get("subtitle", "")
    slug = fm.get("slug", "")
    if not slug:
        fail("Missing 'slug' in frontmatter")
    cover = args.cover_url or fm.get("cover", "")
    tags_str = fm.get("tags", "")
    published_at = fm.get("publishedAt", "")

    # Resolve tags
    tags = resolve_tags(tags_str, pat=pat)

    # Build meta tags
    meta_desc = subtitle or title
    meta_tags = build_meta_tags(title, meta_desc)

    # Build settings
    settings = build_publish_settings(
        delisted=args.delisted,
        newsletter=args.newsletter,
    )

    inp = {
        "title": title,
        "slug": slug,
        "publicationId": pub_id,
        "contentMarkdown": body,
        "metaTags": meta_tags,
        "settings": settings,
    }
    if subtitle:
        inp["subtitle"] = subtitle
    if cover:
        inp["coverImageOptions"] = {"coverImageURL": cover}
    if tags:
        inp["tags"] = tags
    if published_at:
        inp["publishedAt"] = str(published_at)
    if args.series:
        inp["seriesId"] = args.series

    query = """
    mutation PublishPost($input: PublishPostInput!) {
        publishPost(input: $input) {
            post {
                id
                title
                slug
                url
                publishedAt
                series { id name }
                tags { id name slug }
                seo { title description }
            }
        }
    }
    """
    data = graphql(query, {"input": inp}, pat=pat)
    post = data.get("publishPost", {}).get("post", {})
    ok(post, f"Post published: {post.get('url', '')}")


def cmd_post_update(args):
    """Update an existing post."""
    pat, pub_id = get_credentials()

    inp = {"id": args.id}
    if args.title:
        inp["title"] = args.title
    if args.subtitle:
        inp["subtitle"] = args.subtitle
    if args.slug:
        inp["slug"] = args.slug
    if args.content_file:
        _, body = parse_frontmatter(args.content_file)
        inp["contentMarkdown"] = body
    if args.cover_url:
        inp["coverImageOptions"] = {"coverImageURL": args.cover_url}
    if args.tags:
        tags = resolve_tags(args.tags, pat=pat)
        if tags:
            inp["tags"] = tags
    if args.series:
        inp["seriesId"] = args.series
    if args.published_at:
        inp["publishedAt"] = args.published_at

    # Build update settings
    settings = build_update_settings(
        pin=args.pin,
        delisted=args.delisted,
        disable_comments=args.disable_comments,
    )
    inp["settings"] = settings

    # Build meta tags if provided
    if args.meta_title or args.meta_description:
        meta = {}
        if args.meta_title:
            t = args.meta_title
            if BLOG_TITLE_SUFFIX not in t:
                t = t[:60 - len(BLOG_TITLE_SUFFIX)] + BLOG_TITLE_SUFFIX
            meta["title"] = t[:60]
        if args.meta_description:
            meta["description"] = args.meta_description[:160]
        inp["metaTags"] = meta

    query = """
    mutation UpdatePost($input: UpdatePostInput!) {
        updatePost(input: $input) {
            post {
                id
                title
                slug
                url
                publishedAt
                series { id name }
                tags { id name slug }
                seo { title description }
            }
        }
    }
    """
    data = graphql(query, {"input": inp}, pat=pat)
    post = data.get("updatePost", {}).get("post", {})
    ok(post, f"Post updated: {post.get('url', '')}")


def cmd_post_remove(args):
    """Remove (trash) a post."""
    pat, _ = get_credentials()
    query = """
    mutation RemovePost($input: RemovePostInput!) {
        removePost(input: $input) {
            post { id title }
        }
    }
    """
    data = graphql(query, {"input": {"id": args.id}}, pat=pat)
    post = data.get("removePost", {}).get("post", {})
    ok(post, f"Post removed: {post.get('title', '')}")


def cmd_post_restore(args):
    """Restore a removed post."""
    pat, _ = get_credentials()
    query = """
    mutation RestorePost($input: RestorePostInput!) {
        restorePost(input: $input) {
            post { id title slug url }
        }
    }
    """
    data = graphql(query, {"input": {"id": args.id}}, pat=pat)
    post = data.get("restorePost", {}).get("post", {})
    ok(post, f"Post restored: {post.get('title', '')}")


def cmd_post_get(args):
    """Get a post by ID or slug."""
    pat, pub_id = get_credentials()
    identifier = args.id_or_slug

    # If it looks like a slug (no hex ID pattern), query by slug
    if not re.match(r"^[0-9a-f]{24}$", identifier):
        query = """
        query PostBySlug($host: String!, $slug: String!) {
            publication(host: $host) {
                post(slug: $slug) {
                    id title subtitle slug url
                    publishedAt updatedAt
                    brief
                    readTimeInMinutes
                    series { id name slug }
                    tags { id name slug }
                    seo { title description }
                    coverImage { url }
                    author { name username }
                }
            }
        }
        """
        data = graphql(query, {"host": BLOG_DOMAIN, "slug": identifier}, pat=pat)
        post = data.get("publication", {}).get("post")
        if not post:
            fail(f"Post not found with slug: {identifier}")
        ok(post)
    else:
        query = """
        query PostById($id: ID!) {
            post(id: $id) {
                id title subtitle slug url
                publishedAt updatedAt
                brief
                readTimeInMinutes
                series { id name slug }
                tags { id name slug }
                seo { title description }
                coverImage { url }
                author { name username }
            }
        }
        """
        data = graphql(query, {"id": identifier}, pat=pat)
        post = data.get("post")
        if not post:
            fail(f"Post not found with id: {identifier}")
        ok(post)


def cmd_post_list(args):
    """List posts in the publication."""
    pat, _ = get_credentials()
    first = args.first or 10
    query = """
    query ListPosts($host: String!, $first: Int!) {
        publication(host: $host) {
            posts(first: $first) {
                edges {
                    node {
                        id title slug url
                        publishedAt
                        readTimeInMinutes
                        brief
                        series { id name }
                        tags { id name slug }
                    }
                }
                totalDocuments
            }
        }
    }
    """
    data = graphql(query, {"host": BLOG_DOMAIN, "first": first}, pat=pat)
    posts_data = data.get("publication", {}).get("posts", {})
    edges = posts_data.get("edges", [])
    total = posts_data.get("totalDocuments", 0)
    posts = [e["node"] for e in edges]
    ok({"posts": posts, "total": total}, f"Found {total} post(s)")

# ---------------------------------------------------------------------------
# DRAFT commands
# ---------------------------------------------------------------------------

def cmd_draft_create(args):
    """Create a draft from a markdown file."""
    pat, pub_id = get_credentials()
    fm, body = parse_frontmatter(args.file)

    title = fm.get("title", "")
    if not title:
        fail("Missing 'title' in frontmatter")
    subtitle = fm.get("subtitle", "")
    slug = fm.get("slug", "")
    cover = args.cover_url or fm.get("cover", "")
    tags_str = fm.get("tags", "")

    tags = resolve_tags(tags_str, pat=pat)
    settings = build_draft_settings(
        delisted=args.delisted,
        newsletter=args.newsletter,
    )

    inp = {
        "title": title,
        "slug": slug,
        "publicationId": pub_id,
        "contentMarkdown": body,
        "settings": settings,
    }
    if subtitle:
        inp["subtitle"] = subtitle
    if cover:
        inp["coverImageOptions"] = {"coverImageURL": cover}
    if tags:
        inp["tags"] = tags
    if args.series:
        inp["seriesId"] = args.series

    query = """
    mutation CreateDraft($input: CreateDraftInput!) {
        createDraft(input: $input) {
            draft {
                id
                title
                slug
                dateUpdated
                tags { id name slug }
            }
        }
    }
    """
    data = graphql(query, {"input": inp}, pat=pat)
    draft = data.get("createDraft", {}).get("draft", {})
    ok(draft, f"Draft created: {draft.get('title', '')}")


def cmd_draft_publish(args):
    """Publish an existing draft."""
    pat, _ = get_credentials()
    query = """
    mutation PublishDraft($input: PublishDraftInput!) {
        publishDraft(input: $input) {
            post {
                id title slug url publishedAt
            }
        }
    }
    """
    data = graphql(query, {"input": {"draftId": args.id}}, pat=pat)
    post = data.get("publishDraft", {}).get("post", {})
    ok(post, f"Draft published: {post.get('url', '')}")


def cmd_draft_schedule(args):
    """Schedule a draft for future publishing."""
    pat, _ = get_credentials()

    # Parse datetime
    try:
        dt = datetime.fromisoformat(args.datetime.replace("Z", "+00:00"))
        scheduled_at = dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    except ValueError:
        fail(f"Invalid datetime format: {args.datetime}. Use ISO 8601 (e.g., 2026-03-15T10:00:00Z)")

    query = """
    mutation ScheduleDraft($input: ScheduleDraftInput!) {
        scheduleDraft(input: $input) {
            scheduledPost {
                id
                draft { id title slug }
                scheduledDate
            }
        }
    }
    """
    data = graphql(query, {"input": {"draftId": args.id, "publishAt": scheduled_at}}, pat=pat)
    scheduled = data.get("scheduleDraft", {}).get("scheduledPost", {})
    ok(scheduled, f"Draft scheduled for {scheduled_at}")


def cmd_draft_reschedule(args):
    """Reschedule a scheduled draft."""
    pat, _ = get_credentials()

    try:
        dt = datetime.fromisoformat(args.datetime.replace("Z", "+00:00"))
        scheduled_at = dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    except ValueError:
        fail(f"Invalid datetime format: {args.datetime}. Use ISO 8601 (e.g., 2026-03-15T10:00:00Z)")

    query = """
    mutation RescheduleDraft($input: RescheduleDraftInput!) {
        rescheduleDraft(input: $input) {
            scheduledPost {
                id
                scheduledDate
            }
        }
    }
    """
    data = graphql(query, {"input": {"scheduledPostId": args.id, "publishAt": scheduled_at}}, pat=pat)
    scheduled = data.get("rescheduleDraft", {}).get("scheduledPost", {})
    ok(scheduled, f"Draft rescheduled to {scheduled_at}")


def cmd_draft_cancel_schedule(args):
    """Cancel a scheduled draft."""
    pat, _ = get_credentials()
    query = """
    mutation CancelScheduledDraft($input: CancelScheduledDraftInput!) {
        cancelScheduledDraft(input: $input) {
            scheduledPost { id }
        }
    }
    """
    data = graphql(query, {"input": {"scheduledPostId": args.id}}, pat=pat)
    result = data.get("cancelScheduledDraft", {}).get("scheduledPost", {})
    ok(result, "Schedule cancelled")


def cmd_draft_list(args):
    """List drafts in the publication."""
    pat, _ = get_credentials()
    first = args.first or 10
    query = """
    query ListDrafts($host: String!, $first: Int!) {
        publication(host: $host) {
            drafts(first: $first) {
                edges {
                    node {
                        id
                        title
                        slug
                        dateUpdated
                        tags { id name slug }
                        author { name username }
                    }
                }
                totalDocuments
            }
        }
    }
    """
    data = graphql(query, {"host": BLOG_DOMAIN, "first": first}, pat=pat)
    drafts_data = data.get("publication", {}).get("drafts", {})
    edges = drafts_data.get("edges", [])
    total = drafts_data.get("totalDocuments", 0)
    drafts = [e["node"] for e in edges]
    ok({"drafts": drafts, "total": total}, f"Found {total} draft(s)")

# ---------------------------------------------------------------------------
# SERIES commands
# ---------------------------------------------------------------------------

def cmd_series_create(args):
    """Create a new series."""
    pat, pub_id = get_credentials()

    inp = {
        "publicationId": pub_id,
        "name": args.name,
        "slug": args.slug,
        "sortOrder": "dsc",
    }
    if args.description:
        inp["description"] = {"markdown": args.description}

    query = """
    mutation CreateSeries($input: CreateSeriesInput!) {
        createSeries(input: $input) {
            series { id name slug description { markdown } }
        }
    }
    """
    data = graphql(query, {"input": inp}, pat=pat)
    series = data.get("createSeries", {}).get("series", {})
    ok(series, f"Series created: {series.get('name', '')}")


def cmd_series_update(args):
    """Update an existing series."""
    pat, _ = get_credentials()

    inp = {"id": args.id}
    if args.name:
        inp["name"] = args.name
    if args.slug:
        inp["slug"] = args.slug
    if args.description:
        inp["description"] = {"markdown": args.description}
    if args.sort_order:
        inp["sortOrder"] = args.sort_order

    query = """
    mutation UpdateSeries($input: UpdateSeriesInput!) {
        updateSeries(input: $input) {
            series { id name slug description { markdown } sortOrder }
        }
    }
    """
    data = graphql(query, {"input": inp}, pat=pat)
    series = data.get("updateSeries", {}).get("series", {})
    ok(series, f"Series updated: {series.get('name', '')}")


def cmd_series_remove(args):
    """Remove a series."""
    pat, _ = get_credentials()
    query = """
    mutation RemoveSeries($input: RemoveSeriesInput!) {
        removeSeries(input: $input) {
            series { id name }
        }
    }
    """
    data = graphql(query, {"input": {"id": args.id}}, pat=pat)
    series = data.get("removeSeries", {}).get("series", {})
    ok(series, f"Series removed: {series.get('name', '')}")


def cmd_series_add_post(args):
    """Add a post to a series."""
    pat, _ = get_credentials()
    query = """
    mutation AddPostToSeries($input: AddPostToSeriesInput!) {
        addPostToSeries(input: $input) {
            series { id name }
        }
    }
    """
    data = graphql(query, {"input": {"postId": args.post_id, "seriesId": args.series_id}}, pat=pat)
    series = data.get("addPostToSeries", {}).get("series", {})
    ok(series, f"Post added to series: {series.get('name', '')}")


def cmd_series_list(args):
    """List series in the publication."""
    pat, _ = get_credentials()
    first = args.first or 20
    query = """
    query ListSeries($host: String!, $first: Int!) {
        publication(host: $host) {
            seriesList(first: $first) {
                edges {
                    node {
                        id
                        name
                        slug
                        sortOrder
                        description { markdown }
                        posts(first: 3) {
                            totalDocuments
                        }
                    }
                }
                totalDocuments
            }
        }
    }
    """
    data = graphql(query, {"host": BLOG_DOMAIN, "first": first}, pat=pat)
    series_data = data.get("publication", {}).get("seriesList", {})
    edges = series_data.get("edges", [])
    total = series_data.get("totalDocuments", 0)
    series_list = []
    for e in edges:
        node = e["node"]
        node["postCount"] = node.pop("posts", {}).get("totalDocuments", 0)
        series_list.append(node)
    ok({"series": series_list, "total": total}, f"Found {total} series")

# ---------------------------------------------------------------------------
# TAG commands
# ---------------------------------------------------------------------------

def cmd_tag_get(args):
    """Get tag info by slug."""
    pat, _ = get_credentials()
    tag = resolve_tag(args.slug, pat=pat)
    if not tag:
        fail(f"Tag not found: {args.slug}")
    ok(tag, f"Tag found: {tag['name']}")


def cmd_tag_search(args):
    """Search for tags by keyword."""
    pat, _ = get_credentials()
    query = """
    query SearchTags($keyword: String!) {
        searchTags(keyword: $keyword) {
            id
            name
            slug
            postsCount
        }
    }
    """
    # Note: Hashnode may not expose searchTags in public API.
    # Fallback: try tagCategories or individual tag lookups.
    try:
        data = graphql(query, {"keyword": args.query}, pat=pat)
        tags = data.get("searchTags", [])
        ok({"tags": tags, "total": len(tags)}, f"Found {len(tags)} tag(s)")
    except SystemExit:
        # Fallback: try resolving as a single slug
        tag = resolve_tag(args.query, pat=pat)
        if tag:
            ok({"tags": [tag], "total": 1}, "Fell back to exact slug lookup")
        else:
            fail(f"No tags found for: {args.query}")

# ---------------------------------------------------------------------------
# COMMENT commands
# ---------------------------------------------------------------------------

def cmd_comment_add(args):
    """Add a comment to a post."""
    pat, _ = get_credentials()
    query = """
    mutation AddComment($input: AddCommentInput!) {
        addComment(input: $input) {
            comment { id content { markdown } dateAdded }
        }
    }
    """
    inp = {
        "postId": args.post_id,
        "contentMarkdown": args.text,
    }
    data = graphql(query, {"input": inp}, pat=pat)
    comment = data.get("addComment", {}).get("comment", {})
    ok(comment, "Comment added")


def cmd_comment_update(args):
    """Update a comment."""
    pat, _ = get_credentials()
    query = """
    mutation UpdateComment($input: UpdateCommentInput!) {
        updateComment(input: $input) {
            comment { id content { markdown } }
        }
    }
    """
    data = graphql(query, {"input": {"id": args.id, "contentMarkdown": args.text}}, pat=pat)
    comment = data.get("updateComment", {}).get("comment", {})
    ok(comment, "Comment updated")


def cmd_comment_remove(args):
    """Remove a comment."""
    pat, _ = get_credentials()
    query = """
    mutation RemoveComment($input: RemoveCommentInput!) {
        removeComment(input: $input) {
            comment { id }
        }
    }
    """
    data = graphql(query, {"input": {"id": args.id}}, pat=pat)
    comment = data.get("removeComment", {}).get("comment", {})
    ok(comment, "Comment removed")


def cmd_comment_reply(args):
    """Reply to a comment."""
    pat, _ = get_credentials()
    query = """
    mutation AddReply($input: AddReplyInput!) {
        addReply(input: $input) {
            reply { id content { markdown } dateAdded }
        }
    }
    """
    inp = {
        "commentId": args.comment_id,
        "contentMarkdown": args.text,
    }
    data = graphql(query, {"input": inp}, pat=pat)
    reply = data.get("addReply", {}).get("reply", {})
    ok(reply, "Reply added")


def cmd_comment_list(args):
    """List comments on a post."""
    pat, _ = get_credentials()
    first = args.first or 20

    # Comments require the post ID; get via post slug or ID
    identifier = args.post_id

    # If it looks like a slug, resolve to ID first
    if not re.match(r"^[0-9a-f]{24}$", identifier):
        q = """
        query PostBySlug($host: String!, $slug: String!) {
            publication(host: $host) {
                post(slug: $slug) { id }
            }
        }
        """
        d = graphql(q, {"host": BLOG_DOMAIN, "slug": identifier}, pat=pat)
        post = d.get("publication", {}).get("post")
        if not post:
            fail(f"Post not found: {identifier}")
        identifier = post["id"]

    query = """
    query PostComments($id: ID!, $first: Int!) {
        post(id: $id) {
            comments(first: $first, sortBy: RECENT) {
                edges {
                    node {
                        id
                        content { markdown }
                        dateAdded
                        author { name username }
                        replies(first: 5) {
                            edges {
                                node {
                                    id
                                    content { markdown }
                                    dateAdded
                                    author { name username }
                                }
                            }
                        }
                    }
                }
                totalDocuments
            }
        }
    }
    """
    data = graphql(query, {"id": identifier, "first": first}, pat=pat)
    comments_data = data.get("post", {}).get("comments", {})
    edges = comments_data.get("edges", [])
    total = comments_data.get("totalDocuments", 0)
    comments = []
    for e in edges:
        node = e["node"]
        # Flatten replies
        replies_edges = node.get("replies", {}).get("edges", [])
        node["replies"] = [r["node"] for r in replies_edges]
        comments.append(node)
    ok({"comments": comments, "total": total}, f"Found {total} comment(s)")

# ---------------------------------------------------------------------------
# PUB commands
# ---------------------------------------------------------------------------

def cmd_pub_info(args):
    """Get publication info."""
    pat, _ = get_credentials()
    query = """
    query PubInfo($host: String!) {
        publication(host: $host) {
            id
            title
            displayTitle
            descriptionSEO
            about { markdown }
            url
            canonicalURL
            isTeam
            followersCount
            posts(first: 0) { totalDocuments }
            drafts(first: 0) { totalDocuments }
            seriesList(first: 0) { totalDocuments }
        }
    }
    """
    data = graphql(query, {"host": BLOG_DOMAIN}, pat=pat)
    pub = data.get("publication", {})
    if not pub:
        fail("Publication not found")
    # Flatten counts
    pub["totalPosts"] = pub.pop("posts", {}).get("totalDocuments", 0)
    pub["totalDrafts"] = pub.pop("drafts", {}).get("totalDocuments", 0)
    pub["totalSeries"] = pub.pop("seriesList", {}).get("totalDocuments", 0)
    ok(pub, f"Publication: {pub.get('title', '')}")


def cmd_pub_me(args):
    """Get authenticated user info."""
    pat, _ = get_credentials()
    query = """
    query Me {
        me {
            id
            name
            username
            profilePicture
            bio { markdown }
            publications(first: 5) {
                edges {
                    node { id title url }
                }
            }
        }
    }
    """
    data = graphql(query, pat=pat)
    me = data.get("me", {})
    if not me:
        fail("Could not get user info. Check your HASHNODE_PAT.")
    # Flatten publications
    pubs = me.pop("publications", {}).get("edges", [])
    me["publications"] = [e["node"] for e in pubs]
    ok(me, f"Authenticated as: {me.get('username', '')}")


def cmd_pub_stats(args):
    """Get publication stats (posts count, followers, etc.)."""
    pat, _ = get_credentials()
    query = """
    query PubStats($host: String!) {
        publication(host: $host) {
            id
            title
            followersCount
            posts(first: 0) { totalDocuments }
            drafts(first: 0) { totalDocuments }
            seriesList(first: 0) { totalDocuments }
        }
    }
    """
    data = graphql(query, {"host": BLOG_DOMAIN}, pat=pat)
    pub = data.get("publication", {})
    if not pub:
        fail("Publication not found")
    stats = {
        "publicationId": pub.get("id"),
        "title": pub.get("title"),
        "followers": pub.get("followersCount", 0),
        "posts": pub.get("posts", {}).get("totalDocuments", 0),
        "drafts": pub.get("drafts", {}).get("totalDocuments", 0),
        "series": pub.get("seriesList", {}).get("totalDocuments", 0),
    }
    ok(stats, f"Stats for {stats['title']}")

# ---------------------------------------------------------------------------
# WEBHOOK commands
# ---------------------------------------------------------------------------

def cmd_webhook_create(args):
    """Create a webhook."""
    pat, pub_id = get_credentials()

    events = [e.strip().upper() for e in args.events.split(",")]

    query = """
    mutation CreateWebhook($input: CreateWebhookInput!) {
        createWebhook(input: $input) {
            webhook { id url events createdAt }
        }
    }
    """
    inp = {
        "publicationId": pub_id,
        "url": args.url,
        "events": events,
    }
    if args.secret:
        inp["secret"] = args.secret

    data = graphql(query, {"input": inp}, pat=pat)
    webhook = data.get("createWebhook", {}).get("webhook", {})
    ok(webhook, f"Webhook created: {webhook.get('url', '')}")


def cmd_webhook_update(args):
    """Update a webhook."""
    pat, _ = get_credentials()

    inp = {"id": args.id}
    if args.url:
        inp["url"] = args.url
    if args.events:
        inp["events"] = [e.strip().upper() for e in args.events.split(",")]
    if args.secret:
        inp["secret"] = args.secret

    query = """
    mutation UpdateWebhook($input: UpdateWebhookInput!) {
        updateWebhook(input: $input) {
            webhook { id url events }
        }
    }
    """
    data = graphql(query, {"input": inp}, pat=pat)
    webhook = data.get("updateWebhook", {}).get("webhook", {})
    ok(webhook, f"Webhook updated: {webhook.get('url', '')}")


def cmd_webhook_delete(args):
    """Delete a webhook."""
    pat, _ = get_credentials()
    query = """
    mutation DeleteWebhook($input: DeleteWebhookInput!) {
        deleteWebhook(input: $input) {
            webhook { id }
        }
    }
    """
    data = graphql(query, {"input": {"id": args.id}}, pat=pat)
    webhook = data.get("deleteWebhook", {}).get("webhook", {})
    ok(webhook, "Webhook deleted")


def cmd_webhook_test(args):
    """Trigger a test event for a webhook."""
    pat, _ = get_credentials()
    # Note: Hashnode may not have a test mutation. We'll try triggerWebhookTest.
    query = """
    mutation TriggerWebhookTest($input: TriggerWebhookTestInput!) {
        triggerWebhookTest(input: $input) {
            webhook { id }
        }
    }
    """
    try:
        data = graphql(query, {"input": {"webhookId": args.id}}, pat=pat)
        ok(data, "Webhook test triggered")
    except SystemExit:
        fail("Webhook test not supported by Hashnode API")


def cmd_webhook_list(args):
    """List webhooks."""
    pat, _ = get_credentials()
    query = """
    query ListWebhooks($host: String!) {
        publication(host: $host) {
            webhooks {
                id
                url
                events
                createdAt
            }
        }
    }
    """
    data = graphql(query, {"host": BLOG_DOMAIN}, pat=pat)
    webhooks = data.get("publication", {}).get("webhooks", [])
    ok({"webhooks": webhooks, "total": len(webhooks)}, f"Found {len(webhooks)} webhook(s)")

# ---------------------------------------------------------------------------
# REDIRECT commands
# ---------------------------------------------------------------------------

def cmd_redirect_create(args):
    """Create a URL redirect."""
    pat, pub_id = get_credentials()

    inp = {
        "publicationId": pub_id,
        "source": args.source,
        "destination": args.destination,
        "type": int(args.type) if args.type else 301,
    }

    query = """
    mutation CreateRedirectionRule($input: CreateRedirectionRuleInput!) {
        createRedirectionRule(input: $input) {
            redirectionRule { id source destination type }
        }
    }
    """
    data = graphql(query, {"input": inp}, pat=pat)
    rule = data.get("createRedirectionRule", {}).get("redirectionRule", {})
    ok(rule, f"Redirect created: {rule.get('source', '')} -> {rule.get('destination', '')}")


def cmd_redirect_update(args):
    """Update a redirect rule."""
    pat, _ = get_credentials()

    inp = {"id": args.id}
    if args.source:
        inp["source"] = args.source
    if args.destination:
        inp["destination"] = args.destination
    if args.type:
        inp["type"] = int(args.type)

    query = """
    mutation UpdateRedirectionRule($input: UpdateRedirectionRuleInput!) {
        updateRedirectionRule(input: $input) {
            redirectionRule { id source destination type }
        }
    }
    """
    data = graphql(query, {"input": inp}, pat=pat)
    rule = data.get("updateRedirectionRule", {}).get("redirectionRule", {})
    ok(rule, f"Redirect updated: {rule.get('source', '')} -> {rule.get('destination', '')}")


def cmd_redirect_remove(args):
    """Remove a redirect rule."""
    pat, _ = get_credentials()
    query = """
    mutation DeleteRedirectionRule($input: DeleteRedirectionRuleInput!) {
        deleteRedirectionRule(input: $input) {
            redirectionRule { id }
        }
    }
    """
    data = graphql(query, {"input": {"id": args.id}}, pat=pat)
    rule = data.get("deleteRedirectionRule", {}).get("redirectionRule", {})
    ok(rule, "Redirect removed")


def cmd_redirect_list(args):
    """List redirect rules."""
    pat, _ = get_credentials()
    query = """
    query ListRedirects($host: String!) {
        publication(host: $host) {
            redirectionRules {
                id
                source
                destination
                type
            }
        }
    }
    """
    data = graphql(query, {"host": BLOG_DOMAIN}, pat=pat)
    rules = data.get("publication", {}).get("redirectionRules", [])
    ok({"redirects": rules, "total": len(rules)}, f"Found {len(rules)} redirect(s)")

# ---------------------------------------------------------------------------
# Argparse setup
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hashnode-api",
        description="Manage Hashnode blog via GraphQL API. All output is JSON.",
    )
    subparsers = parser.add_subparsers(dest="group", help="Command group")

    # --- post ---
    post_parser = subparsers.add_parser("post", help="Manage posts")
    post_sub = post_parser.add_subparsers(dest="command")

    p = post_sub.add_parser("publish", help="Publish a post from markdown file")
    p.add_argument("file", help="Path to markdown file with frontmatter")
    p.add_argument("--series", help="Series ID to assign the post to")
    p.add_argument("--delisted", action="store_true", help="Hide from community feed")
    p.add_argument("--newsletter", action="store_true", help="Send as newsletter")
    p.add_argument("--cover-url", help="Override cover image URL")
    p.set_defaults(func=cmd_post_publish)

    p = post_sub.add_parser("update", help="Update an existing post")
    p.add_argument("id", help="Post ID")
    p.add_argument("--title", help="New title")
    p.add_argument("--subtitle", help="New subtitle")
    p.add_argument("--slug", help="New slug")
    p.add_argument("--content-file", help="Markdown file for new content")
    p.add_argument("--cover-url", help="Cover image URL")
    p.add_argument("--tags", help="Comma-separated tag slugs")
    p.add_argument("--series", help="Series ID")
    p.add_argument("--published-at", help="Published date (ISO 8601)")
    p.add_argument("--pin", action="store_true", default=None, help="Pin to blog")
    p.add_argument("--no-pin", dest="pin", action="store_false", help="Unpin from blog")
    p.add_argument("--delisted", action="store_true", default=None, help="Hide from community feed")
    p.add_argument("--no-delisted", dest="delisted", action="store_false", help="Show in community feed")
    p.add_argument("--disable-comments", action="store_true", default=None, help="Disable comments")
    p.add_argument("--enable-comments", dest="disable_comments", action="store_false", help="Enable comments")
    p.add_argument("--meta-title", help="SEO meta title")
    p.add_argument("--meta-description", help="SEO meta description")
    p.set_defaults(func=cmd_post_update)

    p = post_sub.add_parser("remove", help="Remove (trash) a post")
    p.add_argument("id", help="Post ID")
    p.set_defaults(func=cmd_post_remove)

    p = post_sub.add_parser("restore", help="Restore a removed post")
    p.add_argument("id", help="Post ID")
    p.set_defaults(func=cmd_post_restore)

    p = post_sub.add_parser("get", help="Get a post by ID or slug")
    p.add_argument("id_or_slug", help="Post ID (24-char hex) or slug")
    p.set_defaults(func=cmd_post_get)

    p = post_sub.add_parser("list", help="List published posts")
    p.add_argument("--first", type=int, default=10, help="Number of posts (default: 10)")
    p.set_defaults(func=cmd_post_list)

    # --- draft ---
    draft_parser = subparsers.add_parser("draft", help="Manage drafts")
    draft_sub = draft_parser.add_subparsers(dest="command")

    p = draft_sub.add_parser("create", help="Create a draft from markdown file")
    p.add_argument("file", help="Path to markdown file with frontmatter")
    p.add_argument("--series", help="Series ID")
    p.add_argument("--delisted", action="store_true", help="Delist when published")
    p.add_argument("--newsletter", action="store_true", help="Send as newsletter when published")
    p.add_argument("--cover-url", help="Cover image URL")
    p.set_defaults(func=cmd_draft_create)

    p = draft_sub.add_parser("publish", help="Publish an existing draft")
    p.add_argument("id", help="Draft ID")
    p.set_defaults(func=cmd_draft_publish)

    p = draft_sub.add_parser("schedule", help="Schedule a draft")
    p.add_argument("id", help="Draft ID")
    p.add_argument("datetime", help="Publish time (ISO 8601, e.g., 2026-03-15T10:00:00Z)")
    p.set_defaults(func=cmd_draft_schedule)

    p = draft_sub.add_parser("reschedule", help="Reschedule a scheduled draft")
    p.add_argument("id", help="Scheduled post ID")
    p.add_argument("datetime", help="New publish time (ISO 8601)")
    p.set_defaults(func=cmd_draft_reschedule)

    p = draft_sub.add_parser("cancel-schedule", help="Cancel a scheduled draft")
    p.add_argument("id", help="Scheduled post ID")
    p.set_defaults(func=cmd_draft_cancel_schedule)

    p = draft_sub.add_parser("list", help="List drafts")
    p.add_argument("--first", type=int, default=10, help="Number of drafts (default: 10)")
    p.set_defaults(func=cmd_draft_list)

    # --- series ---
    series_parser = subparsers.add_parser("series", help="Manage series")
    series_sub = series_parser.add_subparsers(dest="command")

    p = series_sub.add_parser("create", help="Create a series")
    p.add_argument("name", help="Series name")
    p.add_argument("slug", help="Series slug")
    p.add_argument("--description", help="Series description (plain text)")
    p.set_defaults(func=cmd_series_create)

    p = series_sub.add_parser("update", help="Update a series")
    p.add_argument("id", help="Series ID")
    p.add_argument("--name", help="New name")
    p.add_argument("--slug", help="New slug")
    p.add_argument("--description", help="New description (plain text)")
    p.add_argument("--sort-order", choices=["asc", "dsc"], help="Sort order")
    p.set_defaults(func=cmd_series_update)

    p = series_sub.add_parser("remove", help="Remove a series")
    p.add_argument("id", help="Series ID")
    p.set_defaults(func=cmd_series_remove)

    p = series_sub.add_parser("add-post", help="Add a post to a series")
    p.add_argument("post_id", help="Post ID")
    p.add_argument("series_id", help="Series ID")
    p.set_defaults(func=cmd_series_add_post)

    p = series_sub.add_parser("list", help="List series")
    p.add_argument("--first", type=int, default=20, help="Number of series (default: 20)")
    p.set_defaults(func=cmd_series_list)

    # --- tag ---
    tag_parser = subparsers.add_parser("tag", help="Look up Hashnode tags")
    tag_sub = tag_parser.add_subparsers(dest="command")

    p = tag_sub.add_parser("get", help="Get tag by slug")
    p.add_argument("slug", help="Tag slug (e.g., javascript)")
    p.set_defaults(func=cmd_tag_get)

    p = tag_sub.add_parser("search", help="Search tags by keyword")
    p.add_argument("query", help="Search keyword")
    p.set_defaults(func=cmd_tag_search)

    # --- comment ---
    comment_parser = subparsers.add_parser("comment", help="Manage comments")
    comment_sub = comment_parser.add_subparsers(dest="command")

    p = comment_sub.add_parser("add", help="Add a comment to a post")
    p.add_argument("post_id", help="Post ID or slug")
    p.add_argument("text", help="Comment text (markdown)")
    p.set_defaults(func=cmd_comment_add)

    p = comment_sub.add_parser("update", help="Update a comment")
    p.add_argument("id", help="Comment ID")
    p.add_argument("text", help="New comment text (markdown)")
    p.set_defaults(func=cmd_comment_update)

    p = comment_sub.add_parser("remove", help="Remove a comment")
    p.add_argument("id", help="Comment ID")
    p.set_defaults(func=cmd_comment_remove)

    p = comment_sub.add_parser("reply", help="Reply to a comment")
    p.add_argument("comment_id", help="Comment ID to reply to")
    p.add_argument("text", help="Reply text (markdown)")
    p.set_defaults(func=cmd_comment_reply)

    p = comment_sub.add_parser("list", help="List comments on a post")
    p.add_argument("post_id", help="Post ID or slug")
    p.add_argument("--first", type=int, default=20, help="Number of comments (default: 20)")
    p.set_defaults(func=cmd_comment_list)

    # --- pub ---
    pub_parser = subparsers.add_parser("pub", help="Publication info and stats")
    pub_sub = pub_parser.add_subparsers(dest="command")

    p = pub_sub.add_parser("info", help="Get publication info")
    p.set_defaults(func=cmd_pub_info)

    p = pub_sub.add_parser("me", help="Get authenticated user info")
    p.set_defaults(func=cmd_pub_me)

    p = pub_sub.add_parser("stats", help="Get publication stats")
    p.set_defaults(func=cmd_pub_stats)

    # --- webhook ---
    webhook_parser = subparsers.add_parser("webhook", help="Manage webhooks")
    webhook_sub = webhook_parser.add_subparsers(dest="command")

    p = webhook_sub.add_parser("create", help="Create a webhook")
    p.add_argument("url", help="Webhook URL")
    p.add_argument("--events", required=True,
                   help="Comma-separated events (e.g., POST_PUBLISHED,POST_UPDATED)")
    p.add_argument("--secret", help="Webhook secret for signature verification")
    p.set_defaults(func=cmd_webhook_create)

    p = webhook_sub.add_parser("update", help="Update a webhook")
    p.add_argument("id", help="Webhook ID")
    p.add_argument("--url", help="New URL")
    p.add_argument("--events", help="Comma-separated events")
    p.add_argument("--secret", help="New secret")
    p.set_defaults(func=cmd_webhook_update)

    p = webhook_sub.add_parser("delete", help="Delete a webhook")
    p.add_argument("id", help="Webhook ID")
    p.set_defaults(func=cmd_webhook_delete)

    p = webhook_sub.add_parser("test", help="Test a webhook")
    p.add_argument("id", help="Webhook ID")
    p.set_defaults(func=cmd_webhook_test)

    p = webhook_sub.add_parser("list", help="List webhooks")
    p.set_defaults(func=cmd_webhook_list)

    # --- redirect ---
    redirect_parser = subparsers.add_parser("redirect", help="Manage URL redirects")
    redirect_sub = redirect_parser.add_subparsers(dest="command")

    p = redirect_sub.add_parser("create", help="Create a redirect")
    p.add_argument("source", help="Source path (e.g., /old-post)")
    p.add_argument("destination", help="Destination path (e.g., /new-post)")
    p.add_argument("--type", default="301", choices=["301", "302"], help="Redirect type (default: 301)")
    p.set_defaults(func=cmd_redirect_create)

    p = redirect_sub.add_parser("update", help="Update a redirect")
    p.add_argument("id", help="Redirect rule ID")
    p.add_argument("--source", help="New source path")
    p.add_argument("--destination", help="New destination path")
    p.add_argument("--type", choices=["301", "302"], help="Redirect type")
    p.set_defaults(func=cmd_redirect_update)

    p = redirect_sub.add_parser("remove", help="Remove a redirect")
    p.add_argument("id", help="Redirect rule ID")
    p.set_defaults(func=cmd_redirect_remove)

    p = redirect_sub.add_parser("list", help="List redirects")
    p.set_defaults(func=cmd_redirect_list)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.group:
        parser.print_help()
        sys.exit(0)

    if not hasattr(args, "func"):
        # Group was given but no command
        # Find the subparser for this group and print its help
        for action in parser._subparsers._actions:
            if isinstance(action, argparse._SubParsersAction):
                if args.group in action.choices:
                    action.choices[args.group].print_help()
                    break
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
