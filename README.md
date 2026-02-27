# tail -f thoughts

**Um blog de engenharia de software por Vinicius Carvalho.**
*A software engineering blog by Vinicius Carvalho.*

---

## O que é / What is it

**PT-BR**: Blog pessoal onde compartilho experiências, erros, acertos e reflexões sobre desenvolvimento de software, liderança técnica e arquitetura. Publicado no [Hashnode](https://tail-f-thoughts.hashnode.dev) com sync automático via GitHub.

**EN**: Personal blog sharing experiences, mistakes, wins, and reflections on software development, tech leadership, and architecture. Published on [Hashnode](https://tail-f-thoughts.hashnode.dev) with automatic GitHub sync.

## Estrutura / Structure

```
articles/
├── published/    # Artigos publicados (auto-sync com Hashnode)
├── drafts/       # Rascunhos em andamento (saveAsDraft: true)
└── ideas/        # Ideias e outlines (ignorePost: true)
assets/
└── images/       # Imagens locais
templates/        # Templates de artigo
scripts/          # Scripts de automação
```

## Workflow

```
idea → draft → review → publish → auto-sync
```

1. **Idea**: Crie um outline em `articles/ideas/` com `ignorePost: true`
2. **Draft**: Desenvolva o artigo em `articles/drafts/` com `saveAsDraft: true`
3. **Review**: Revise voz, SEO e formatação
4. **Publish**: Mova para `articles/published/` removendo `saveAsDraft`
5. **Auto-sync**: O Hashnode GitHub App publica automaticamente no commit

## Setup

1. Clone o repositório
2. Copie `.env.example` para `.env` e preencha suas credenciais
3. Execute `bash scripts/hashnode-setup.sh` para validar a configuração
4. Instale o [Hashnode GitHub App](https://hashnode.com/apps/github) no repositório
5. Use `/blog-post` no Claude Code para criar artigos

## Tech Stack

- **Plataforma**: [Hashnode](https://hashnode.com) com GitHub source integration
- **Escrita**: Claude Code com skill `/blog-post`
- **Formato**: Markdown com frontmatter YAML
- **Deploy**: Auto-publish via Hashnode GitHub App

---

*"tail -f" = seguir o fluxo dos pensamentos em tempo real*
