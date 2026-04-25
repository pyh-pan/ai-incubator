# Project Archive

This archive preserves durable context distilled from the historical `CLAUDE.md`. It is reference material, not an active instruction file.

## Product Principles

AI Incubator is an AI-assisted idea incubation tool. Its core principle is to make the user's thinking visible instead of replacing it. The product should guide users through focused questions, structured refinement, and a visual workspace.

The current product direction is intentionally simple: one fixed, general thinking framework. Historical multi-framework ideas can be reconsidered later, but they should not drive current implementation complexity.

## Historical Lessons Worth Keeping

- Local development and automated tests must not depend on live AI providers. Model failures should fall back to deterministic behavior.
- Authentication errors should be explicit and consistent, especially for missing or invalid tokens.
- UI behavior around the workspace should remain stable after answering nodes, creating follow-ups, and refreshing data.
- React Flow interactions need regression coverage when layout, node state, handles, or edges change.
- End-to-end tests should cover only critical user journeys and use stable selectors.
- Documentation should record decisions and constraints, not duplicate the full code structure.

## Retired Or Deferred Ideas

- User-visible framework selection and framework editing are deferred.
- Custom framework prompts, framework recommendation, and framework-specific project initialization are deferred.
- Large historical changelogs, old test counts, personal session metadata, and generated screenshots/logs should not be restored into active docs.

## Reference Notes

Historical versions experimented with richer framework management, settings pages, React Flow layout refinements, AI-generated branch questions, and extensive Playwright coverage. These may be useful as design references, but current development should optimize for a smaller, reliable core.
