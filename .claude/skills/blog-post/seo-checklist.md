# SEO Checklist — tail -f thoughts

Run through this checklist before moving any article to `articles/published/`.

## Title Optimization

- [ ] Length: 50-60 characters
- [ ] Contains primary keyword naturally (not forced)
- [ ] Compelling — would you click on this?
- [ ] No clickbait — delivers on the promise
- [ ] Unique across the publication (check existing articles)

## Meta Description (subtitle field)

- [ ] Length: 150-160 characters
- [ ] Contains primary keyword
- [ ] Includes a value proposition (what the reader gets)
- [ ] Ends with a hook or question when appropriate
- [ ] Different from the title — adds new information

## Slug

- [ ] Lowercase, hyphen-separated
- [ ] 3-6 words maximum
- [ ] Contains primary keyword
- [ ] No stop words (a, the, is, etc.) unless needed for clarity
- [ ] Unique across the publication

## Content Structure

- [ ] First paragraph contains primary keyword naturally
- [ ] H2 headings break content into scannable sections
- [ ] At least one H2 contains a keyword variation
- [ ] Paragraphs: 2-4 sentences max (scannable on mobile)
- [ ] Total word count: 1000-2500 words
- [ ] TL;DR or key takeaway near the top

## Tags

- [ ] 3-5 tags selected
- [ ] Tags exist on Hashnode (use established tags, not custom ones)
- [ ] Primary technology/topic is first tag
- [ ] Mix of specific (e.g., "React") and broad (e.g., "Web Development")

## Images and Media

- [ ] Cover image set (Hashnode CDN URL preferred)
- [ ] Cover image is relevant and not generic stock
- [ ] All images have alt text (for accessibility and SEO)
- [ ] Code blocks have language specified
- [ ] Mermaid diagrams used for complex flows (renders natively on Hashnode)

## Internal Linking

- [ ] References to previous articles where relevant
- [ ] Uses descriptive anchor text (not "click here")
- [ ] Links open to valid published URLs

## Engagement Signals

- [ ] Ends with a call to action (question, share prompt, or discussion invite)
- [ ] Personal voice maintained throughout (not generic/corporate)
- [ ] Provides actionable takeaways the reader can use immediately

## Frontmatter Final Check

```yaml
---
title: "..."           # 50-60 chars
subtitle: "..."        # 150-160 chars (meta description)
slug: keyword-slug     # 3-6 words
cover: https://...     # Hashnode CDN
domain: tail-f-thoughts.hashnode.dev
tags: tag1, tag2, tag3 # 3-5 tags
publishedAt: ...       # ISO 8601 date
---
```

- [ ] `domain` is set to `tail-f-thoughts.hashnode.dev`
- [ ] `saveAsDraft: true` removed (for publishing)
- [ ] `publishedAt` date is correct
- [ ] No `ignorePost` flag present
