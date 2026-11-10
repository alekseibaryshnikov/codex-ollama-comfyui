# Clarity review for working applications

Apply this protocol alongside [contemporary visual design](contemporary-visual-design.md) to new apps and substantial redesigns. Clarity and visual craft are separate requirements; passing these workflow checks does not make a visually generic screen finished. Treat the examples and numeric defaults as design policy for this skill, not as measured universal thresholds. Keep the product's actual users and constraints in control.

## 1. Establish the screen contract

Write one sentence for the user's result: "A warehouse operator can find a part, compare depot quantities, and record a correct stock change." Follow it with the decision, required facts, action, visible completion, and recovery. Do not start by assigning a sidebar, card grid, font pairing, or aesthetic category.

List the principal information objects and their relationships. For scheduling they may be date, time, room, and session; for an approval queue they may be request, evidence, decision, and owner. Let those relationships determine the spatial arrangement. Retain known conventions so users do not have to learn a novel control system.

If the product or audience is not supplied, use a small, explicit assumption. Ask only when a missing fact would change the workflow materially. Never claim a persona, interview, preference study, or usability finding that was not actually obtained.

## 2. Review what the first screen communicates

Answer these questions from the interface itself, without reading an assistant's accompanying explanation:

| Question | Evidence that should be visible | Failure to correct |
| --- | --- | --- |
| Where am I? | A concise title and necessary workspace/date/location context | Several repeated titles, vague slogans, or decorative greetings |
| What matters here? | Relevant records, the important exception, or the active task | A wall of equally emphasized cards or unrelated summary numbers |
| What can I do next? | A named primary action or a consistent action for each record | A hidden row interaction, unexplained icon, or competing primary buttons |
| What exactly will change? | The affected object and scope, with old/new values when helpful | A generic action with an unclear target or a global status hiding local conditions |
| What happened? | Updated content and a clear result close to the task | A transient message with stale data or an inaccessible toast |
| How do I recover? | A usable cancel, back, edit, retry, or undo path | Nested dialogs, lost input, vanished focus, or the wrong item selected |

A quick first-impression check is useful for spotting weak hierarchy. Do not label it a "five-second test" unless people actually completed a timed test. A designer's or agent's answer is a hypothesis about usability.

## 3. Reduce unnecessary decisions

- Classify each major region as current work, necessary context, or a secondary/recovery action. Remove or defer a region without a task-related purpose.
- Keep the common action where users work. Choose a compact labeled action, discoverable row activation, or contextual selection tools for the workload. Avoid both hidden interactions and a large button strip repeated in every row. Preserve keyboard and touch access.
- Give one editing surface the needed context and inputs. A details dialog followed by a second editing dialog needs a real reason; a single form often removes an avoidable step.
- Separate global navigation, page tools, and record actions. A viewer used to compare demos must not look like another layer of product navigation.
- Show the most useful controls immediately. Group infrequent tools under a labeled, understandable secondary control when appropriate. Do not hide frequent actions just to reduce the button count.
- Preserve expert efficiency: shortcuts and bulk tools may coexist with a clear visible path. Do not turn a well-understood frequent task into a long wizard.
- Use labels that predict the effect. "Update stock", "Save session", and "Export visible rows" describe scope more clearly than a generic "Manage" or "Apply".
- Present error correction at the affected fields and keep prior input. Name the conflict and the practical remedy when one is known.

## 4. Make meaning precise

**Attach status to its subject.** If North depot has 56 items and South has zero, show the South shortage beside the South quantity. Do not label the whole part "Out of stock" without qualification. Explain whether a threshold applies per location or to a total.

**Align the comparison.** Put units and attributes in stable positions. For a schedule, make simultaneous sessions and room assignments comparable. For a financial or measurement chart, show the actual unit, scale, and period. For a list grouped by start time, avoid implying that visual row height represents duration; show start/end times explicitly.

**Expose active scope.** Keep date, location, room, search, or filter selection visible. Distinguish an empty dataset from a filtered view with no matches. Label exports and bulk actions with their actual scope.

**Make completion unambiguous.** Update the relevant data, show a concise receipt, and make recovery usable. If a modal remains open, a background toast is not an operable place for its Undo action. If the changed record leaves a filter, explain the result and move focus to a useful visible control.

## 5. Make the information easy to read

- Start with body and form text at 16 px, dense records at 14–16 px, and secondary metadata at 12–13 px. Keep essential names, quantities, dates, and actions out of tiny text. Preserve these roles on mobile by recomposing the layout.
- Use a small, deliberate type hierarchy. Let the page title establish context, section titles group work, and record text carry the details. A large heading is justified by its role, not by a desire to look premium.
- Give related items tighter proximity and unrelated groups more space. Prefer alignment, separators, and spacing to repeated panels when they communicate grouping clearly.
- Use action color, selection, and semantic status deliberately. Keep warning/error meanings stable and add text or another non-color cue. Do not use pale secondary text to make dense content seem quieter.
- Retain visible control boundaries, useful field labels, and high-contrast focus indicators on every surface, including dark navigation and notifications.
- Keep rows, dates, and labels readable with long realistic content. Allow wrapping and height growth. Use truncation only when the full value is easily available and is not required for the current decision.
- On touch layouts, favor comfortable 44 px controls while observing the precise WCAG requirements in the quality reference. Do not make a phone version by reducing all type and control sizes.

### Preserve useful density

Compare substantial revisions at the same viewport with representative data. Record the first useful row or working object's vertical position, useful content visible, number of header/toolbar bands, and essential context retained. Removing boxes or enlarging spacing is not automatically an improvement. Correct duplicated page titles, over-tall control bands, and repeated large action buttons that displace the work.

Use compact spacing within a record and larger spacing between meaningful groups. As working desktop heuristics, 44–64 px can suit a one-line data row and 64–76 px a two-line row; allow more space when actual content requires it. These are neither required dimensions nor accessibility standards. Do not impose touch-size defaults on every desktop toolbar, and do not increase raw row count by hiding decision-critical information.

## 6. Inspect a representative workflow

Choose an actual scenario and realistic data before checking:

1. Start from the first screen with no explanation from the creator.
2. Identify the relevant item or time period and the facts needed for the decision.
3. Open the intended action through the visible controls.
4. Make one valid change and check its exact scope and result.
5. Enter one meaningful invalid value or conflict; correct it without re-entering unrelated information.
6. Cancel or undo and confirm both data and focus return sensibly.
7. Repeat the essential task on a narrow layout and with keyboard input when browser tools are available.

Inspect one representative screen early, before replicating its composition. In later passes, retest the views affected by actual changes. Distinguish observations from assumptions; do not keep polishing preferences after the concrete task risks have been resolved.

### Delivery evidence

| Evidence | What it can support | What it cannot establish |
| --- | --- | --- |
| Source inspection | Intended structure, labels, relationships, many correctness defects | Actual layout, clipping, visual hierarchy, or browser focus behavior |
| Unit/state checks, including a DOM stub | Tested logic and state transitions under the test assumptions | A rendered interface or complete browser interactions |
| Rendered desktop/mobile inspection | What was visible in the inspected states and viewports | Universal usability, every device, or a complete accessibility audit |
| Task tests with representative users | Observed success, hesitation, errors, and feedback for those tasks and participants | A guarantee that all users will find the app obvious |

When browser or preview infrastructure is unavailable, report that early and at delivery, follow the supported delivery workflow, and keep visual verification marked incomplete. Do not change access controls, replace restricted preview infrastructure, or invent screenshots or user-test results to remove the limitation.

## Sources and interpretation

The operational protocol above is this skill's synthesis. Its concrete screen questions, examples, and typography defaults are design decisions, not quotations or new research findings.

- [GOV.UK Government Design Principles](https://www.gov.uk/guidance/government-design-principles): supports starting from user needs, resolving complexity, considering context, and iterating. This is an interaction-design reference, not a requirement to imitate GOV.UK's visual identity.
- [GOV.UK Service Standard: Make the service simple to use](https://www.gov.uk/service-manual/service-standard/point-4-make-the-service-simple-to-use): pairs simplicity with testing actual and potential users across relevant devices and the full service.
- [Nielsen Norman Group: 10 Usability Heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/): informs visible status, familiar language, consistency, error prevention, recovery, and prioritizing relevant information. These are broad heuristics, not a certification checklist.
- [Nielsen Norman Group: Memory Recognition and Recall in User Interfaces](https://www.nngroup.com/articles/recognition-and-recall/): supports supplying relevant cues and choices in context, reducing the information users must retrieve from memory.

Reviewed 19 October 2026. Read the separate research notes for dated 2026 developments and explicitly provisional 2027 directions.
