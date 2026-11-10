---
name: design-web-apps
description: Design and implement modern web-app UI/UX with a distinctive visual identity, clear tasks, readable information, precise composition, and complete interactions. Use automatically when creating, redesigning, styling, or improving a web app, dashboard, SaaS product, admin panel, portal, tracker, app screen, or responsive frontend, including Russian-language requests. Apply alongside the relevant build skill. Skip backend-only work, infrastructure, ordinary prose, and standalone image or slide design.
---

# Modern Web App Design

Use this as a reusable standard for design judgment, implementation, and review. Make the user's next decision and action immediately understandable, and give the product a considered, contemporary visual identity. Both outcomes are required.

## Two quality gates: usability and visual craft

This user explicitly rejects generic ChatGPT dashboards and dated-looking bare interfaces. They want clear UI/UX with fresh visual design. The previous Relay inventory and Gather scheduling examples were rejected; do not reuse either as an approved template. A palette change, larger type, or removal of panels alone did not satisfy the brief.

Treat **usable behavior** and **visual craft** as independent acceptance gates. Choose the task model, composition, and art direction together before implementation. A clear but visually generic screen is unfinished; a striking screen with unclear actions is also unfinished. Accessibility and truthful behavior apply throughout. Preserve familiar controls while giving the work an identifiable visual character. Do not defer design identity to a final cosmetic pass or equate simplicity with sparse, oversized forms.

For new apps and substantive redesigns, read both [contemporary visual design](references/contemporary-visual-design.md) and [the clarity review](references/clarity-review.md) before implementation and use them at delivery. The visual reference guide supplies inspected examples, source dates, a concrete art-direction contract, and a density review. Numerical defaults are working heuristics, not universal laws or accessibility certification.

Research baseline: **19 October 2026**. Treat 2027 directions as forecasts. Read [the research notes](references/research-2026-2027.md) when choosing a dated direction or explaining the evidence. Read [the quality checks](references/quality-checks.md) for implementation review and precise standards. Keep the workflow applicable without a fresh trend search on every small edit; verify changing facts and technical compatibility whenever they affect a decision.

## 1. Establish the product before styling

- Identify the primary user, main task, usage frequency, expertise, content volume, and important device or input constraints. Separate supplied facts from reasonable assumptions; do not invent user research.
- Inspect the existing app, project instructions, component system, tokens, fonts, assets, and representative screens. Follow the current brief and project conventions. Reuse the implementation stack unless the task calls for changing it.
- Use brand context only for its associated product. Do not carry a previous project's palette, voice, or layout into unrelated apps.
- Infer routine choices and proceed. Ask only when a missing answer would materially change the product, principal workflow, or required deliverable. Do useful reversible work first; do not require a style questionnaire or approval of every screen.
- Use the relevant building and delivery skill, including Sites where applicable. This skill supplies design guidance; it does not replace runtime, hosting, storage, permissions, or deployment rules.
- Match effort to scope. For a small fix, inspect the surrounding screen, preserve the design language, and review affected states. For a new app or substantial redesign, follow the complete workflow.

For substantial work, establish a compact screen contract alongside the visual direction:

1. **User and situation:** who is doing the work, with what knowledge and constraints?
2. **Task:** what concrete result do they need from this screen?
3. **Decision:** what must they understand or choose next?
4. **Necessary evidence:** which facts must be visible together to make that decision?
5. **Action and scope:** what can they do, to which item, location, period, or selection?
6. **Completion and recovery:** what visibly changes, and how can they correct a mistake?
7. **Small-screen equivalent:** how can the same task be completed without tiny text or missing facts?

Keep this brief internal or in existing project design guidance; it is not a questionnaire or a block of explanatory UI copy. Use it with inspected references to resolve structure, action hierarchy, density, type, palette, and character as one composition. For a small change, apply only the relevant parts.

## 2. Choose structure from the work

| Work to support | Useful starting structure | Protect |
| --- | --- | --- |
| Compare or manage many records | Table or structured list with search, filters, and detail | Scan speed, comparable attributes, selection, recovery |
| Triage a queue | List and detail workspace | Position, selected item, next action, return path |
| Create or edit an artifact | Content canvas with contextual tools | Working space, save state, undo, preview |
| Complete an occasional transaction | Focused form or short sequence | Clear labels, progress when useful, input retention |
| Track stages of work | Board when stages matter; list when comparison matters | Status meaning and equivalent non-drag actions |
| Monitor performance | Decision-oriented overview with relevant drill-down | Units, time period, provenance, actionable changes |
| Plan time-bound work | Calendar or timeline when time organizes the work | Date context, conflicts, useful list alternatives |

- Make the main work and next useful action apparent in the first viewport. Keep supporting navigation quieter while maintaining readable contrast and discoverable controls.
- Make the page understandable without the assistant's explanation. A user should be able to identify its purpose, read the relevant state, and locate the next action from the actual interface. Use a quick first-impression review as a heuristic; do not claim a timed usability result without a real test.
- Give every major visible region a job: performing the task, supplying necessary context, or providing a relevant recovery/secondary action. Remove or defer regions without one. Keep frequently needed actions discoverable; fewer visible controls is not automatically better.
- Use one dominant action treatment for the current task, with consistent item actions in repeated records. This does not mean an arbitrary one-button limit. Avoid several unrelated actions competing for the same emphasis.
- Allocate space according to task importance. Avoid a large greeting, decorative hero, or invented KPI row displacing the actual work in an operational app.
- Keep equivalent controls in predictable locations. Distinguish global navigation, page tools, and item actions.
- Show information needed for the current decision together. Reveal secondary detail progressively without hiding comparison-critical facts.
- Put state next to its true subject and show its scope. A shortage at one depot must not make a part look unavailable everywhere. Show dates, units, rooms, and active filters at the level where their meaning is needed. Align simultaneous events or comparable values; do not make users reconstruct them from disconnected cards.
- Use cards for genuinely separate objects or modules. Use alignment, proximity, whitespace, rows, and subtle separators when those express the structure better. Do not wrap every label or section in another rounded box.
- Include search, filters, bulk actions, shortcuts, or command search when the workload benefits; preserve visible paths for common actions.
- Make opening an item lead to the useful next step. Prefer direct editing when inspection and editing use the same facts; avoid a details dialog followed by another modal solely to reach an Edit form. Use a persistent detail pane only when side-by-side inspection or repeated triage warrants its space.
- Choose record actions for the workload: a compact labeled link, discoverable row activation, or contextual tools beside a selection may be appropriate. Do not turn every row into a large outlined button strip. Keep common actions discoverable, keyboard accessible, and available without hover on touch devices.

## 3. Commit to a coherent visual direction

For a new app or substantial redesign, inspect approximately three relevant actual product views: one for the workflow, one for visual character, and one for controls or interaction. A reference can serve several roles. Use supplied references and the guide before searching further; browse when currentness or an unfamiliar detail matters. Record the source, date or access date, device, and what was actually seen. A landing page, mobile screenshot, internal editor, or promotional composite is not proof of the current desktop app. If reference images cannot be viewed, mark that gap rather than inventing observations.

Consider two materially different compositions internally and choose one against the brief. Specify the dominant working surface; shell and content proportions; density; typography roles; palette and color behavior; geometry and elevation; imagery when relevant; and one purposeful interaction detail. Explain how the choices work together. "Premium", "editorial", "minimal", or a list of fashionable font names is not an art direction. See the [art-direction contract](references/contemporary-visual-design.md#art-direction-contract).

Examples of appropriate variation:

- **Operational workspace:** a precise data grid or timeline, compact controls, selective strong color, a coherent neutral shell, and detail beside the selected object when useful.
- **Creative workspace:** a dominant canvas, expressive content, well-proportioned contextual tools, and a distinctive treatment of previews and selection.
- **Consumer experience:** recognizable content imagery, confident typography and color, comfortable controls, and a focused task sequence.

Treat these as directions, not templates or compulsory palettes. Expression also belongs inside working apps: schedule blocks, image collections, maps, record identity, and carefully designed interactions can carry it. Use a coherent visual system rather than averaging unrelated references or copying a company's brand.

### Typography

- Start with the existing or approved font. Otherwise choose one readable UI family with suitable language coverage; add a second display family only when it improves the identity. A common font is acceptable when used well.
- Define semantic roles: page title, section title, body, label, metadata, and numeric data. Use a restrained set of sizes, weights, and line heights across screens.
- Default to 16 px for body/form text and 14–16 px for dense working records. Reserve 12–13 px for genuinely secondary metadata. Do not put information needed to decide or act in 8–11 px text. Preserve essential text size on phones and allow names, labels, and rows to wrap. These are this skill's readability defaults, not WCAG minimum font sizes; respect a proven existing system where appropriate.
- Give operational pages proportionate headings; reserve oversized display text for suitable brand moments. Use tabular numerals and aligned units where users compare values.
- Test long names, translated labels, numbers, and realistic content. Use logical alignment and relevant script coverage; do not assume English-only lengths or Latin-only fonts.

### Color, spacing, and shape

- Define or reuse semantic tokens for canvas, surface, elevated surface, primary/secondary text, border, action, focus, and success/warning/error. Centralize raw values and use role names in components.
- Choose one dominant action treatment, supported by a deliberate neutral palette and semantic status colors. Additional colors must encode meaning or serve the brand.
- Compose hierarchy through size, weight, position, grouping, color, and whitespace together. Keep operational headings proportionate to the work. A poster can anchor an event detail page; the scheduling view should give time and sessions the main space. Avoid repeated headers or generic greetings. Maintain visible field boundaries and sufficiently strong secondary text.
- Use a consistent spacing rhythm. A 4 px base with 4/8/12/16/24/32/48/64 steps is a useful starting point, not a law. Allow optical corrections; make grouping and hierarchy visibly coherent.
- Distinguish compact control spacing from group spacing and page spacing. Whitespace must help grouping and scanning; adding it everywhere can push the useful work below the fold. Inspect the first useful record or working object and the amount of meaningful content visible at the target viewport.
- Use a small radius and elevation vocabulary appropriate to the product. Give elevation a real layering purpose. Match icons in family, stroke, scale, and optical alignment; avoid emoji as generic interface icons.
- Preserve readability in secondary text, disabled states, placeholders, and charts. Color alone must not communicate selection, status, or errors.
- Implement requested themes well. Do not add a dark-mode switch as decoration or expand every small task into a second theme. When multiple themes exist, use semantic tokens and verify each.

### Depth and motion

- Default to opaque content surfaces for tables, forms, and reading. Use translucent navigation or floating controls only when it strengthens hierarchy and stays readable on real backgrounds; provide an opaque fallback. Avoid stacked blur layers.
- Use motion to explain state, spatial relationships, or feedback. Short transitions around 120–240 ms are a starting heuristic; adjust to the interaction and platform. Do not delay completion for animation.
- Plan selection, expansion, rearrangement, and completion behavior with the static composition. A consistent response to input can supply character without making the interface busy; motion is not a late layer of arbitrary fades.
- Respect reduced-motion preferences and preserve equivalent feedback. Avoid scroll hijacking, cursor replacements, perpetual decorative movement, or heavy 3D effects unless explicitly warranted and usable.

## 4. Design the behavior with the appearance

- Build the complete primary journey within the requested scope. Every visible control must work or clearly communicate its limitation. Never present a placeholder backend, synthetic metric, or simulated transaction as live functionality.
- Define applicable states before polishing: default, hover, focus, pressed, selected, disabled, loading, empty, success, error, and permission-limited. Do not manufacture irrelevant states.
- Label actions with clear verbs and objects. Prefer sentence case and product-specific, natural copy. Replace filler, invented testimonials, fake urgency, and unexplained jargon with meaningful content.
- Use the language of the action: "Update stock", "Save session", or "Export visible rows" instead of an ambiguous "Manage", "Continue", or a lone symbol. Repeat the affected record or scope in an editing surface. Explain only genuinely ambiguous choices; do not surround simple controls with marketing copy or tutorials.
- Keep form labels visible; use appropriate input types, autocomplete, instructions, and associated validation. Preserve data after errors, give a useful correction, and expose submission outcomes.
- Distinguish first-use emptiness, no matching results, and an error. Give the appropriate next step: create/import, adjust filters, or retry. Avoid generic illustrations replacing an explanation.
- Acknowledge input immediately. Preserve existing useful content during refresh; localize pending feedback to the affected region. Use genuine stages or percentages only when known. Support cancellation or background continuation for longer work when feasible.
- Prefer undo for easily reversible actions. Use an exact, reviewable confirmation at genuinely consequential commitment points. Do not add confirmation to every routine action.
- Keep the success receipt and recovery controls usable in the active surface. An Undo toast behind a still-open modal is not a usable recovery path. After a change moves an item out of a filter, preserve understandable context and restore focus to a connected, visible target.
- Preserve navigation and task context across opening details, filtering, editing, and returning. Support normal browser history and meaningful URLs when the stack and scope allow.
- In tables, use realistic column priorities, formatting, sorting, selection, and overflow behavior. In charts, show units, period, scale, and relevant comparison; provide an accessible summary or equivalent data. Do not add decorative charts with arbitrary numbers.

## 5. Compose for the available space

- Use intrinsic Grid/Flexbox layouts; let content determine breakpoints. Use container queries for components that adapt to allocated space and subgrid when shared alignment helps. Verify target-browser support for the exact feature and preserve a usable fallback.
- Recompose navigation and multi-pane workflows on narrow screens. Choose what becomes a drawer, separate detail view, stacked section, or scrollable data region. Preserve primary-task capability and a clear return path.
- Avoid a fixed desktop canvas squeezed onto a phone. Do not hide essential columns or actions merely to fit; provide an intentional alternative or contained horizontal scrolling where two-dimensional data requires it.
- Keep touch targets comfortably operable. A 44×44 CSS px target is a useful touch default; WCAG 2.2 AA's minimum is 24×24 with specific exceptions, not a universal 44 px rule.
- Support reflow at 320 CSS px equivalent width and text enlargement to 200%, with the standard's stated exceptions. Do not apply a table's two-dimensional-layout exception to the whole app shell.
- Check sticky bars, safe areas, drawers, focus visibility, and virtual-keyboard effects where relevant. Avoid layouts that hide the active field or final action.

## 6. Build accessibility and performance into the system

- Target WCAG 2.2 AA; recognize that this skill is not a complete conformance audit. Use semantic HTML and established accessible primitives before custom ARIA widgets.
- Provide keyboard operation, visible focus, meaningful names, logical headings/landmarks, appropriate image alternatives, and status announcements. Keep modal focus contained and restore it appropriately; provide an explicit close path.
- Meet text contrast of 4.5:1, or 3:1 for qualifying large text. Meet applicable 3:1 non-text contrast requirements. Verify actual foreground/background combinations. See the precise [accessibility checks](references/quality-checks.md#accessibility).
- Provide a non-drag single-pointer alternative for drag interactions; keyboard support is also necessary. Permit password managers and paste in authentication flows.
- Reserve media dimensions, manage font loading, avoid unexpected layout shifts, and keep the main interaction responsive. Avoid heavy dependencies or visual effects without a clear benefit.
- Use Core Web Vitals as field-performance goals: LCP ≤2.5 s, INP ≤200 ms, CLS ≤0.1 at the 75th percentile, evaluated separately for mobile and desktop. Lab diagnostics do not prove field results; see [performance checks](references/quality-checks.md#performance).

## 7. Apply AI patterns only when the product calls for AI

- Embed assistance beside the task it improves. Preserve direct controls for comparing, selecting, editing, and committing. Do not turn every workflow into a blank chat box.
- Use buttons, checkboxes, structured fields, and editable previews for bounded decisions; retain free text when useful. Keep generated controls inside an accessible, predictable component vocabulary.
- Distinguish source records, AI suggestions, previews, and applied changes. Show relevant evidence or sources when available; never fabricate citations, confidence percentages, capabilities, or progress.
- Let users correct, dismiss, retry, stop, or undo where appropriate. Make consequential actions and data access understandable before commitment. Surface permissions at the relevant moment instead of adding blanket warning screens.
- Explain capabilities in product language. Keep navigation stable; make adaptive behavior understandable and controllable. Treat fully self-rearranging interfaces as an experiment, not a 2027 default.

## 8. Review the rendered product and finish

For meaningful implementation work, check the permitted preview/browser capability early. Build one representative primary screen with realistic data and its main interaction before multiplying its layout into more screens. Inspect that screen at working desktop and phone sizes when rendering is available; correct the structure before spreading it. A build, DOM stub, or code read does not establish visual quality.

1. Inspect representative desktop and mobile views; include an intermediate width for layouts that change there. Look at the first viewport and the full task.
2. Complete the primary journey with pointer and keyboard. Check relevant loading, empty, error, success, and long-content states. Review affected themes and motion preferences. Inspect the actual parsed form controls and their options; a successful script or DOM-stub check can miss broken markup that blocks the user.
3. Apply the [clarity review](references/clarity-review.md): explain what a new user can identify, compare, and do from the screen itself. Check hierarchy, alignment, typography, contrast, responsive behavior, focus, and truthful feedback. Do not award a subjective score and treat it as evidence.
4. Apply the separate [visual acceptance review](references/contemporary-visual-design.md#visual-acceptance-review). Compare the render with the chosen references for composition, type hierarchy, control precision, surfaces, and coherent character. For revisions, compare the same viewport and representative data: work start position, visible useful records, competing header bands, and lost context. Removing panels must not silently halve useful visible content. Preserve necessary detail; raw row count is not the sole goal.
5. Fix concrete defects in either gate and recheck affected views. Stop when the task and chosen visual direction are sufficiently verified; do not use preference churn as a reason to leave a visibly generic or unreviewed screen. Avoid unrelated redesign or repeated testing without a concrete remaining risk.
6. Report structural and visual decisions and what was actually tested. Name observable changes when a user rejects an earlier design. Distinguish source review, unit/state checks, rendered inspection, and testing with representative users. Provider-generated screenshots can establish the visible layout in captured states, but cannot establish interactive behavior. If rendering is unavailable, continue the work allowed by the delivery workflow and mark visual verification incomplete. Do not claim the interface is visually validated, intuitive to all users, or production ready. Do not bypass permitted preview infrastructure to manufacture proof.

Use [the acceptance checklist](references/quality-checks.md#acceptance-checklist) before delivery. Fix known critical task, keyboard, overflow, or readability failures within scope. Keep implementation details out of the app's user experience unless they help its users make a decision.

## Guardrails against generic output

- Do not treat purple gradients, bento cards, glass, giant headings, dark mode, a particular font, or a fashionable neutral palette as automatic evidence of quality.
- Do not accept a palette-only revision when the user rejects generic design. Revisit the information model, primary action, navigation, density, and sequence; name the concrete differences in the result.
- Do not replace a generic dashboard with an equally generic bare table, giant form, repeated header stack, or oversized outlined controls. Show a deliberate composition and visual system in the actual render.
- Do not clone a reference product's identity; extract the useful pattern and adapt it to this brief.
- Do not remove useful labels, shrink contrast, or hide navigation to make a screen appear cleaner.
- Do not use arbitrary statistics, meaningless badges, mismatched icons, repetitive boxes, or a generic marketing layout to fill a working app.
- Do not trade the main workflow, accessibility, performance, or product coherence for a trend. Use 2026 evidence as context and 2027 forecasts as optional hypotheses.
