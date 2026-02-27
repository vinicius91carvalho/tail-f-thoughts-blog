---
name: blog-post
description: Create blog posts for "tail -f thoughts" following established voice, workflow, and quality standards. Use when writing new blog content, creating article outlines, drafting posts, or publishing articles.
argument-hint: "[topic or title]"
---

# /blog-post — Blog Post Creation Skill

Create blog posts for "tail -f thoughts" following the established voice, workflow, and quality standards.

The user may provide a topic/title as argument: $ARGUMENTS

## Before you start

Read these files to understand the voice, rules, and examples:
1. `CLAUDE.md` — Project rules, voice summary, frontmatter rules
2. [voice-guide.md](voice-guide.md) — Detailed voice patterns and anti-AI checklist
3. [seo-checklist.md](seo-checklist.md) — SEO validation checklist
4. [examples/sample-post.md](examples/sample-post.md) — Example post demonstrating all conventions

## Process

This skill follows a 4-phase process. **Do not skip phases.** Each phase produces a file that can be reviewed before proceeding.

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

**Goal**: Validate voice authenticity, SEO, and anti-AI patterns.

Run through these three checklists on the draft:

#### Voice check (from voice-guide.md)
- [ ] Reads like Vinicius, not like a AI-generated article
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
2. Ensure cover image is set (remind user to upload to Hashnode CDN if needed)
3. Set final `publishedAt` date
4. Remove `saveAsDraft: true` from frontmatter
5. Move file from `articles/drafts/` to `articles/published/`
6. Delete the outline from `articles/ideas/` (no longer needed)
7. **Do NOT commit yet** — confirm with the user first, as committing to `articles/published/` triggers auto-publish

**Output**: `articles/published/<slug>.md` ready for commit

---

## Quick Reference

| Phase | Command | Output |
|-------|---------|--------|
| 1 | "outline" or "idea" | `articles/ideas/<slug>.md` |
| 2 | "draft" or "write" | `articles/drafts/<slug>.md` |
| 3 | "review" | Updated draft |
| 4 | "finalize" or "publish" | `articles/published/<slug>.md` |

## Files to read before writing

- `CLAUDE.md` — Project rules and voice summary
- [voice-guide.md](voice-guide.md) — Detailed voice patterns
- [seo-checklist.md](seo-checklist.md) — SEO validation
- [examples/sample-post.md](examples/sample-post.md) — Example post
- `templates/article-template.md` — Blank template structure
