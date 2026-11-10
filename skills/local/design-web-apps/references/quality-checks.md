# Web-app quality checks

Use this reference to check a working interface and resolve concrete usability risks. Preserve the project's established components, tokens, navigation, and interaction conventions unless the task authorizes changing them. Scale verification to the change: a narrow edit needs checks of the affected component, states, and breakpoints; a new application needs a representative complete journey.

Standards and documentation checked on **2026-10-19**. Treat numeric accessibility requirements separately from optional design heuristics. Recheck changing browser support when it affects an implementation decision.

## Contents

- [Accessibility](#accessibility)
- [Interaction and content](#interaction-and-content)
- [Responsive composition](#responsive-composition)
- [Performance](#performance)
- [Acceptance checklist](#acceptance-checklist)

## Accessibility

Target WCAG 2.2 AA, including applicable Level A criteria. Use the complete standard when evaluating conformance; the checks below are a practical selection. The published [WCAG 2.2 Recommendation](https://www.w3.org/TR/WCAG22/) is dated 12 December 2024. Never claim conformance from a short checklist or an automated score.

### Contrast and focus

- Maintain text contrast of **4.5:1**, or **3:1** for large text: at least 18 pt regular or 14 pt bold, approximately 24 or 18.67 CSS px. Check secondary text and placeholders too. Apply the standard's exceptions appropriately; do not round a failing ratio upward. See [SC 1.4.3](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html).
- Give visual information necessary to recognize controls, states, and meaningful graphics **3:1 contrast against adjacent colors**. Decorative borders do not all need this ratio; inactive controls have an exception. Check colors in the rendered state, including translucent backgrounds. See [SC 1.4.11](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html).
- Keep keyboard focus visible and prevent author-created overlays or sticky regions from entirely hiding the focused component. Prefer keeping it completely visible. These AA requirements are [SC 2.4.7](https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html) and [SC 2.4.11](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html).
- Use a clearly contrasting 2–3 px outline as a practical default. Do not describe that thickness as an AA rule. **AAA SC 2.4.13** requires a qualifying indicator area at least equivalent to a 2 CSS px perimeter and a 3:1 contrast change between the same pixels in focused and unfocused states. Adjacent-color contrast is a separate check. See [Focus Appearance](https://www.w3.org/WAI/WCAG22/Understanding/focus-appearance.html).

### Targets, text, and input

- Make pointer targets at least **24 × 24 CSS px** for AA, subject to spacing, equivalent-control, inline, unmodified user-agent, and essential-presentation exceptions. For undersized targets, centered 24 px diameter circles must not intersect another target or another undersized target's circle. Prefer **44 × 44 CSS px** for important touch controls as a stronger ergonomic default; 44 px corresponds to the AAA enhanced criterion. See [SC 2.5.8](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html).
- Preserve information and functionality at **320 CSS px width** for ordinary vertically scrolling content without requiring two-dimensional scrolling. Horizontally scrolling content uses 256 CSS px height. Necessary two-dimensional content, such as maps and data tables, has exceptions; surrounding controls and ordinary text must still adapt. See [SC 1.4.10](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html).
- Support effective text enlargement to **200%** without lost content or functionality, with the stated captions/images-of-text exceptions. Check that responsive rules do not defeat enlargement. See [SC 1.4.4](https://www.w3.org/WAI/WCAG22/Understanding/resize-text.html).
- Preserve functionality when users override line height to 1.5×, paragraph spacing to 2×, letter spacing to 0.12×, and word spacing to 0.16× font size. These are resilience tests, not mandatory typography defaults; script-specific exceptions apply. See [SC 1.4.12](https://www.w3.org/WAI/WCAG22/Understanding/text-spacing.html).
- Make task functionality keyboard-operable. For dragging features, also provide a **single-pointer alternative without dragging**, such as move controls or a numeric input. Keyboard shortcuts alone do not satisfy the separate dragging requirement. See [SC 2.5.7](https://www.w3.org/WAI/WCAG22/Understanding/dragging-movements.html).
- Allow password managers and paste. Avoid authentication that requires an unsupported cognitive-function test; ensure any segmented code field accepts a complete pasted code when paste provides the transcription alternative. See [SC 3.3.8](https://www.w3.org/WAI/WCAG22/Understanding/accessible-authentication-minimum.html).

### Motion

Respect [`prefers-reduced-motion`](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@media/prefers-reduced-motion): remove or replace nonessential spatial motion while preserving meaningful progress and state feedback. This is a strong default, not a blanket AA requirement to use that media query. Disabling nonessential interaction-triggered motion is [AAA SC 2.3.3](https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html).

Separately, [A SC 2.2.2](https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html) requires pause/stop/hide for automatically starting moving, blinking, or scrolling information that lasts over five seconds alongside other content, unless essential. Auto-updating information has a separate provision without the five-second condition. Avoid decorative perpetual motion in task interfaces.

## Interaction and content

Use native semantic controls or established accessible primitives. Use links for navigation and buttons for actions. Keep visible labels where practical; associate every input with a programmatic label. Do not substitute placeholders for labels. Group related controls and make requirements clear before submission. See [W3C labeling guidance](https://www.w3.org/WAI/tutorials/forms/labels/).

Provide concise errors that explain the correction and identify the affected field. Preserve entered values. Associate field errors with their inputs; consider a linked error summary for longer forms. Make completion explicit and distinguish pending work from success. See [W3C form notifications](https://www.w3.org/WAI/tutorials/forms/notifications/).

Expose displayed saving, progress, result-count, and error status messages to assistive technology without unnecessary focus changes. Use appropriate live-region semantics; reserve assertive announcements for urgent information. Do not announce entire result lists or every streaming token as a status update. See [SC 4.1.3](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html).

Give modal dialogs an accessible name, appropriate initial focus, contained tab sequence, explicit close/cancel control, Escape behavior, inert background, and logical focus restoration. Prefer native `dialog.showModal()` or a proven primitive, then verify the actual behavior. Return focus to the invoker unless the completed workflow makes another destination appropriate. See the [WAI modal pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/) and [MDN dialog guidance](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/dialog).

For each relevant component, inspect default, focus, selected, disabled, pending, empty, error, and success states. Include hover/pressed states where applicable. Avoid dead controls, unexplained disabled actions, fabricated successful saves, or placeholders presented as live data. State prototype limitations honestly. Use realistic content lengths, useful empty-state actions, and clear consequences for destructive actions; provide undo when feasible.

## Responsive composition

Use **390 / 768 / 1440 CSS px** as sample mobile/tablet/desktop inspection widths, not universal requirements. Adapt to the product's audience and existing breakpoints; separately test the 320 px accessibility condition. Inspect intermediate widths when the layout changes, not only preset device sizes.

Recompose navigation, tools, and content around task priority. Do not merely shrink the desktop interface. Keep essential actions reachable, make intentional table overflow apparent, and avoid page-wide overflow, clipped menus, or fixed bars covering content. Stress long names, translations, large numbers, and empty collections. Check supported themes and relevant writing directions.

Use intrinsic Grid/Flex layouts and [container size queries](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Containment/Container_queries) where reusable components must respond to their allocated space. Keep essential behavior usable without optional visual enhancements; use [`@supports`](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@supports) where fallbacks are needed. Verify exact feature support for the project's browser targets. [Baseline](https://developer.mozilla.org/en-US/docs/Glossary/Baseline/Compatibility) summarizes browser compatibility; it does not establish accessibility, performance, webview, or assistive-technology support.

## Performance

Target the following **field** thresholds at the **75th percentile**, assessing mobile and desktop separately. Meet all three for a good Core Web Vitals result:

| Metric | Good threshold |
|---|---:|
| Largest Contentful Paint (LCP) | ≤ 2.5 seconds |
| Interaction to Next Paint (INP) | ≤ 200 milliseconds |
| Cumulative Layout Shift (CLS) | ≤ 0.1 |

Source: [Core Web Vitals thresholds](https://web.dev/articles/defining-core-web-vitals-thresholds), updated 7 May 2025; [Web Vitals](https://web.dev/articles/vitals).

Use Lighthouse and browser profiling to diagnose risks. A local run cannot prove real-user performance. Exercise actual interactions; page-load-only tests do not establish INP, and TBT is not interchangeable with it. Inspect post-load shifts too. [Lab and field measurements differ](https://web.dev/articles/lab-and-field-data-differences); [CrUX API data](https://developer.chrome.com/docs/crux/api/) aggregates the preceding 28 days.

Reserve space for images, embeds, and asynchronous content; prevent avoidable font and layout shifts. Load critical content promptly and never lazy-load the LCP image. Select asset sizes and dependencies appropriate to the product, and profile costly effects when they create a concrete risk. See [Optimize CLS](https://web.dev/articles/optimize-cls) and [Optimize LCP](https://web.dev/articles/optimize-lcp).

## Acceptance checklist

- Run the interface and inspect its actual render at relevant widths; screenshots supplement interaction checks.
- Apply both the [clarity review](clarity-review.md) and the [visual acceptance review](contemporary-visual-design.md#visual-acceptance-review). A working but visually generic screen does not satisfy a new-app design brief. Check the render against the chosen art direction and relevant product references.
- For a substantial revision, compare the same viewport and representative content. Check where useful work starts, how much is visible, repeated header bands, and the context retained. More whitespace or fewer panels alone is not evidence of improvement.
- Complete a representative primary journey and verify the affected keyboard, focus, form, and dialog behavior.
- Inspect applicable loading, empty, error, success, permission, and content-extreme states.
- Check contrast, target sizing, enlargement/reflow, and reduced motion where the change affects them.
- Run available, appropriate diagnostics and required project checks. Distinguish observed results from assumptions.
- Fix concrete defects and recheck the affected experience. Stop once material risks and required gates are resolved; do not expand a minor edit into speculative redesign or repetitive testing.
- Report what changed, what was actually checked, and any material limitation. Do not claim unrun tests, fabricated metrics, full conformance, or quality proven by a score.

Automated accessibility tools cannot evaluate every requirement and can produce misleading results. Combine them with human judgment and practical interaction checks, as explained in [W3C evaluation guidance](https://www.w3.org/WAI/test-evaluate/tools/selecting/).
