---
name: codebase-bootstrap
description: Use when setting up a new project for agent-assisted development — analyzes codebase structure and generates a CLAUDE.md/AGENTS.md with build commands, conventions, and architecture notes.
---

# Codebase Bootstrap

## Overview

Analyze an existing codebase and produce a project instruction file (CLAUDE.md or AGENTS.md) that enables effective agent-assisted development in future sessions.

## When to Use

- Setting up a new project for the first time with an AI coding agent
- Refreshing outdated project instructions after major refactors
- Creating a CLAUDE.md for a repository that lacks one

## Process

### 1. Discover project identity

```
Read: README.md, pyproject.toml / Cargo.toml / package.json / Makefile
Identify: language, framework, package manager, entry points
```

### 2. Map project structure

```
List top-level directories (max depth 2)
Identify: source layout, test location, config files, scripts
Note: monorepo structure if applicable
```

### 3. Extract build/test/lint commands

Look for commands in this priority order:
1. Makefile targets
2. Package manager scripts (npm scripts, cargo commands)
3. CI config (.github/workflows/*.yml, Justfile)
4. README instructions

Required entries:
- **Build**: how to compile/install
- **Test**: how to run tests
- **Lint**: how to check code quality
- **Dev**: how to run in development mode

### 4. Identify conventions

- Code style (formatter, linter config)
- Naming patterns (files, functions, classes)
- Import style (absolute vs relative)
- Test organization (co-located vs separate directory)
- Coordinate system (0-based vs 1-based, if applicable)

### 5. Write the instruction file

Format as markdown with these sections:

```markdown
# Project Name

## What this is
One paragraph.

## Commands
| Action | Command |
|--------|---------|
| Build  | ...     |
| Test   | ...     |
| Lint   | ...     |

## Architecture
Key modules and their responsibilities.

## Conventions
Coding rules specific to this project.

## Validation commands
Commands to run before considering work complete.
```

### 6. Verify

Run the test and lint commands to confirm they work. Fix obvious broken commands before finalizing.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Inventing commands that don't exist | Only document commands you've actually run |
| Listing every file | Summarize modules, not files |
| Missing the test command | Always verify `test` works end-to-end |
| Forgetting coordinate systems | Note 0-based vs 1-based if bioinformatics |
| Writing in wrong language | Match the project's primary language for section headers; body can be bilingual |
