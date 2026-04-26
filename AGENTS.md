# Repository Guidelines

## Purpose

This file defines the working contract for coding agents contributing to this repository. Keep it focused on durable engineering rules, not project history, generated status notes, or file-by-file documentation.

## Product Direction

Preserve the current product direction unless the user explicitly changes it: a simple AI-assisted idea incubation workspace using one fixed, general thinking framework. Do not add user-visible multi-framework selection, settings complexity, or large workflow branches without approval.

The AI should help users clarify their own thinking. Favor questions, structure, and visual feedback over replacing the user's judgment with generated conclusions.

## Development Workflow

Read the existing code before changing behavior. Prefer small, coherent changes that match local patterns over broad rewrites. Keep unrelated cleanup out of feature or bugfix patches.

When local and remote code disagree, do not merge blindly. Identify the product intent, preserve current working behavior, and manually port only the useful parts.

Use worktrees for larger integration or refactor work. Never revert user changes or destructive-edit the working tree unless explicitly instructed.

This repository is solo-maintained. When the user asks to ship completed work, merge directly into `main` and push to the remote; do not create or recommend a pull request unless the user explicitly asks for one.

## Implementation Standards

Keep backend API contracts explicit and tested. Authentication-protected endpoints must return consistent `401` responses for missing or invalid credentials.

AI-dependent flows must have deterministic fallback behavior so local development and tests do not require external model access. External model calls should be bounded by timeouts and clear provider configuration.

Frontend changes should keep the workspace dense, direct, and usable. Avoid decorative UI, nested cards, and explanatory in-app text. Preserve interaction clarity, responsive layout, and accessible labels for controls.

## Testing Requirements

Run targeted tests for every behavior change. Add regression tests for API contracts, auth behavior, AI fallback paths, and core workspace interactions.

Use backend unit tests for service and API guarantees, frontend unit tests for components/hooks/stores, and Playwright only for critical end-to-end flows. Do not update tests just to match broken behavior.

## Documentation Rules

Keep `AGENTS.md` concise and durable. Move historical context, retired decisions, and migration notes into `docs/` when they are useful for future review.

Do not recreate `CLAUDE.md`; this project is maintained through Codex/OpenCode-style agents. If agent-specific notes are needed, add them here or in focused docs.

## Agent Tooling

Use gstack `/browse` for all web browsing. Never use `mcp__claude-in-chrome__*` tools.

Before finalizing, report the verification commands that were run and any commands that could not be run.
