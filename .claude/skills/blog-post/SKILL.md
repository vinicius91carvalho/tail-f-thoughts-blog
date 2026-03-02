---
name: blog-post
description: Create blog posts for "tail -f thoughts" following established voice, workflow, and quality standards. Use when writing new blog content, creating article outlines, drafting posts, or publishing articles.
argument-hint: "[topic, title, or file path to existing article]"
---

# /blog-post — Blog Post Creation Skill

Create blog posts for "tail -f thoughts" following the established voice, workflow, and quality standards.

The user may provide a topic/title OR a file path as argument: $ARGUMENTS

## Detect input mode

Check the argument to determine which workflow to follow:

- **If the argument is a file path** (ends in `.md`, `.txt`, or starts with `/`, `./`, `~/`, `articles/`): Read the file and use it as the article base. Jump to the **"From existing article"** workflow below.
- **Otherwise**: Treat it as a topic/title. Follow the standard **"From scratch"** workflow (Phase 1 → 2 → 3 → 4).

---

## From existing article

When the user provides their own article as a file:

1. **Read the file** and analyze its contents
2. **Ask the user** which series this belongs to (Thoughts, Vibe Coding Engineering, Building in Public)
3. **Detect the language** (PT or EN) from the content
4. **Save it as a draft** in `articles/drafts/` with proper Hashnode frontmatter (`saveAsDraft: true`, `domain`, slug, tags, etc.). Preserve the author's content — do not rewrite it.
5. **Proceed to Phase 3 (Review)** — run all checklists (fact-check, voice, SEO, technical) on the article
6. Present findings to the user. Suggest improvements but **always ask before changing the author's text** — the author's voice and ideas take priority.
7. After review is approved, proceed to **Phase 4 (Finalize)**

**Key rule**: The author's original content is the base. Enhance and polish, but never overwrite the author's voice or restructure without permission.

## Before you start

Read these files to understand the voice, rules, and examples:
1. `CLAUDE.md` — Project rules, voice summary, frontmatter rules
2. [voice-guide.md](voice-guide.md) — Detailed voice patterns and anti-AI checklist
3. [seo-checklist.md](seo-checklist.md) — SEO validation checklist
4. [examples/sample-post.md](examples/sample-post.md) — Example post demonstrating all conventions

## From scratch

This workflow follows a 4-phase process. **Do not skip phases.** Each phase produces a file that can be reviewed before proceeding.

---

### Phase 1: Topic & Outline

**Goal**: Define the article scope and create a structured outline.

1. Discuss the topic with the user — clarify angle, audience, and key takeaways
2. Choose the language (Portuguese default, English if topic warrants it)
3. Generate a slug: lowercase, hyphenated, 3-6 words with keyword
4. Create an outline file in `articles/ideas/` with this structure:

```markdown
---
title: "Working Title"
slug: the-slug
domain: tail-f-thoughts.hashnode.dev
tags: tag1, tag2, tag3
ignorePost: true
---

## Objetivo
[What the reader should take away]

## Outline
1. Hook — [description]
2. Contexto — [description]
3. Desenvolvimento — [description]
4. Erros/Aprendizados — [description]
5. Exemplo Prático — [description]
6. Conclusão — [description]

## Notas
[Any reference material, links, or raw ideas]
```

**Output**: `articles/ideas/<slug>.md`

---

### Phase 2: Full Draft

**Goal**: Write the complete article following voice guidelines.

1. Read the voice guide: `.claude/skills/blog-post/voice-guide.md`
2. Read the sample post: `.claude/skills/blog-post/examples/sample-post.md`
3. Read the outline from Phase 1
4. Write the full article following these rules:
   - Open with a hook (story, question, or provocative statement)
   - Maintain conversational tone throughout
   - Include at least 1 personal anecdote
   - Include at least 1 code block or mermaid diagram
   - Use colloquial expressions (min 3 in PT, min 2 in EN)
   - Vary sentence length dramatically
   - Target 1000-2500 words
5. Save to `articles/drafts/` with proper frontmatter:

```markdown
---
title: "Final Title (50-60 chars)"
subtitle: "Meta description (150-160 chars)"
slug: the-slug
cover: https://cdn.hashnode.com/res/hashnode/image/upload/placeholder
domain: tail-f-thoughts.hashnode.dev
tags: tag1, tag2, tag3
publishedAt: <today's date>T10:00:00.000Z
saveAsDraft: true
---
```

**Output**: `articles/drafts/<slug>.md`

---

### Phase 3: Review

**Goal**: Validate facts, voice authenticity, SEO, and anti-AI patterns.

Run through these four checklists on the draft:

#### Fact-check (MANDATORY — do this first)
- [ ] **Every factual claim verified** via web search (names, numbers, dates, events)
- [ ] **People's roles/titles are current** and accurate
- [ ] **Statistics and numbers are correct** (book counts, dates, records, etc.)
- [ ] **Historical events described accurately** (locations, participants, outcomes)
- [ ] **Any inaccuracies found**: present to the author with correct data and ask whether to correct or remove the passage
- [ ] **Unverifiable claims flagged**: ask the author for source or suggest tone adjustment

#### Voice check (from voice-guide.md)
- [ ] Reads like Vinicius, not like an AI-generated article
- [ ] Has personal anecdote(s)
- [ ] Uses colloquial expressions naturally
- [ ] Sentence length varies (short + long)
- [ ] Starts some sentences with conjunctions
- [ ] Has at least one self-correction or honest admission
- [ ] No blacklisted AI phrases (check CLAUDE.md list)

#### SEO check (from seo-checklist.md)
- [ ] Title: 50-60 chars with keyword
- [ ] Subtitle/meta: 150-160 chars
- [ ] Slug: 3-6 words with keyword
- [ ] Tags: 3-5 relevant Hashnode tags
- [ ] First paragraph contains keyword
- [ ] Word count in 1000-2500 range
- [ ] Ends with engagement CTA

#### Technical check
- [ ] All code blocks have language specified
- [ ] Code examples are realistic (not placeholder foo/bar)
- [ ] Mermaid diagrams render correctly
- [ ] All links are valid
- [ ] Person mentions include intro + link
- [ ] No accidental personal data or secrets

Present review findings to the user. Fix any issues before proceeding.

**Output**: Updated `articles/drafts/<slug>.md`

---

### Phase 4: Finalize

**Goal**: Prepare the article for publishing.

1. Confirm with user that the draft is approved
2. **Ask the user to provide the cover image URL** — never finalize with a placeholder. Suggest cover ideas relevant to the article theme and recommend these sites:
   - [Unsplash](https://unsplash.com), [Pexels](https://pexels.com), [Pixabay](https://pixabay.com) — free stock photos
   - Hashnode's built-in AI cover generator (dashboard editor)
   - ChatGPT / DALL-E — AI-generated custom covers
   - [unDraw](https://undraw.co), [Storyset](https://storyset.com) — free tech illustrations
   Do not proceed until a real cover image URL is set.
3. Set final `publishedAt` date
4. Remove `saveAsDraft: true` from frontmatter
5. Move file from `articles/drafts/` to `articles/published/`
6. Delete the outline from `articles/ideas/` (no longer needed)
7. **Commit and push** to git
8. **Publish via API** — git push does NOT publish (GitHub App is not configured). Always run:
   ```bash
   python3 scripts/hashnode-api.py post publish articles/published/<slug>.md --series <series_id>
   ```
9. **Verify publication** — run `python3 scripts/hashnode-api.py post get <post_id>` to confirm it's live

**Output**: Article published and verified on Hashnode

---

### Phase 5: LinkedIn Post

**Goal**: Generate a LinkedIn post to promote the article.

After the article is finalized (Phase 4), always generate a LinkedIn promotion post.

**Rules**:
- **Language**: Always Portuguese (BR) — the author's LinkedIn audience is Portuguese-speaking
- **Tone**: Same conversational voice as the blog — informal, direct, like telling a friend. Not corporate LinkedIn-speak.
- **Length**: 400-600 characters MAX. Be succinct. No walls of text, no bullet-point lists, no detailed breakdowns — that's what the article is for.
- **Structure**:
  1. Hook: personal pain point or situation that grabs attention (first 2 lines are visible before "see more")
  2. Brief insight: 1-2 sentences summarizing what you learned or changed (don't explain the whole article)
  3. Link to the article
  4. 3 hashtags max
- **Include**: Link to the article (`https://tail-f-thoughts.hashnode.dev/<slug>`)
- **Hashtags**: 3 max, at the end, no line break before them
- **Anti-corporate patterns**: No "thrilled to announce", "excited to share", "proud to present", no arrows (→), no numbered lists, no emoji. Write like a quick message to a friend.
- **Emoji usage**: Zero. No emoji.

**Output**: LinkedIn post text presented to the user, ready to copy-paste.

---

## Quick Reference

**From scratch** (topic/title):

| Phase | Command | Output |
|-------|---------|--------|
| 1 | "outline" or "idea" | `articles/ideas/<slug>.md` |
| 2 | "draft" or "write" | `articles/drafts/<slug>.md` |
| 3 | "review" | Updated draft |
| 4 | "finalize" or "publish" | `articles/published/<slug>.md` |
| 5 | "linkedin" or automatic | LinkedIn post text (PT-BR) |

**From existing article** (file path):

| Step | What happens | Output |
|------|-------------|--------|
| 1 | Read file, ask series, detect language | — |
| 2 | Save as draft with frontmatter | `articles/drafts/<slug>.md` |
| 3 | Review (fact-check, voice, SEO, technical) | Updated draft |
| 4 | Finalize | `articles/published/<slug>.md` |
| 5 | LinkedIn post | LinkedIn post text (PT-BR) |

## Files to read before writing

- `CLAUDE.md` — Project rules and voice summary
- [voice-guide.md](voice-guide.md) — Detailed voice patterns
- [seo-checklist.md](seo-checklist.md) — SEO validation
- [examples/sample-post.md](examples/sample-post.md) — Example post
- `templates/article-template.md` — Blank template structure
