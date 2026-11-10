---
name: game-reward-design
description: "Build, improve, or review game reward loops using clear event sequences, readable bonus progression, meaningful interaction, and evidence-based repeat-play testing. Use for cascade, multiplier, match-3, slot, and arcade game concepts; reward pacing; bonus design; or game retention and LTV analysis. Not a general animation skill or payout-certification service."
---

# Game Reward Design

Help the player understand what happened, what can still change, and what their action controls. Improve the requested game with the smallest complete change. Treat repeat-play explanations as hypotheses until the relevant behavior is measured.

## Choose the work the user requested

- **Build:** Produce the requested playable implementation or prototype. Begin with one main action, one understandable reward sequence, and a distinctive hook. Add a bonus only if it serves the concept. Don't stop at a design document when implementation was requested.
- **Improve:** Inspect the existing game and its event flow. Find the point where the result becomes confusing, repetitive, passive, or slow. Preserve its identity and change the smallest owning boundary that fixes the problem.
- **Review:** Inspect the supplied game, code, or recording. Give prioritized findings with concrete evidence and a proposed check. A review request alone doesn't authorize implementation.
- **Research:** Separate acquisition, within-session activity, return visits, spending, and LTV. Use [references/evidence-and-metrics.md](references/evidence-and-metrics.md) before interpreting statistics or research.

Don't force gambling mechanics into an unrelated genre, replace the user's engine, or redesign a whole game because a reference title is popular. Follow repository instructions and use the relevant engine skill when implementing.

## Establish the actual loop

Use the project, recordings, rules, and telemetry available. Identify:

- The player's action and what it actually affects.
- The rule that produces a reward or result.
- The intermediate events that can change the result.
- The state that survives an event, round, bonus, or session, and when it resets.
- The displayed result and, for paid play, its full cost and net return.

Write a short event sequence such as `act -> match -> clear -> refill -> apply boost -> settle`. Replace it with the game's real sequence. Match evidence to the exact game edition, mode, speed setting, and recording timestamps. State when inspection was frame-based or sound wasn't auditioned.

For an existing implementation, trace the event producer through state changes, rendering, input, save/reconnect, and settlement callers before editing. Avoid creating a second owner for the same state.

## Pick one design hypothesis

Read [references/design-patterns.md](references/design-patterns.md) for a relevant pattern, its tradeoffs, and acceptance checks. Start with the strongest observed problem or intended hook, not the whole pattern catalogue.

Useful hypotheses from the reference games include:

- **Uncertain improvement:** A result is visible while further legal events can still change it. Show those events and their effect clearly.
- **Bounded progression:** A bonus value or board changes during a feature. Make its effect, duration, eligibility, and reset legible.
- **Direct action:** The player manipulates meaningful objects instead of only requesting an outcome. Explain what their choice affects and what remains random.
- **Proportional feedback:** Distinguish routine events from important ones without delaying control or concealing the result.

For the chosen hypothesis, specify the player-visible change, why it might help, what stays constant, and how to check it. Themed art can make the mechanic recognizable; use original assets and names. Don't copy a reference game's entire feature menu or assume its audience matches this game's audience.

## Keep the result truthful and the state correct

In games with authoritative outcomes, presentation consumes the result. Animation must not reroll it, change settlement, or award it twice. Preserve payout validation, money representation, replay/reconnect behavior, and existing error handling.

For wagering games:

- Distinguish base bet, actual charged action, bonus purchase, gross payout, and net result. A multiplier based on a $1 base bet doesn't make a $200 purchase cost $1.
- Don't present a partial return as a net profit. Keep financial feedback consistent with the actual paid action and bonus purchase.
- Don't invent near misses, imply that losses make a win due, or claim that an input improves expected return without mathematical evidence.
- A growing meter or multiplier must not imply a guaranteed reward unless the rules actually guarantee it.

Explain ordinary non-cash scores and achievements in their own terms. Don't impose money-specific labels on a game that has no wagering.

Keep important state and controls readable, preserve keyboard/touch/gamepad access where supported, and allow celebration skipping or reduced motion where appropriate. A skip changes presentation, never the awarded result.

## Implement and verify the requested change

For code changes, load and follow the project's required SDD/TDD workflow. Specify the changed behavior at its owning source boundary, write the meaningful behavioral test first, observe the expected failure, implement, and verify green. For a behavior-preserving refactor, use passing characterization or existing tests before and after. Prose-only work doesn't need an invented red/green cycle.

Use deterministic outcome fixtures when checking reward presentation. Cover the boundaries the change actually touches, such as a zero return, return below cost, qualifying and non-qualifying boosts, bonus reset, repeated events, skip, or reconnect. Don't add irrelevant tests or claim that fixture playback validates RNG, RTP, live transactions, or player enjoyment.

For design validation, hold outcomes and costs constant when comparing presentation. Measure whether players can explain the result and whether they enjoy or voluntarily choose the experience. Separate those checks from adequately sized cohort tests of return behavior. Don't label small exploratory samples as proof of retention.

No public statistics or short playtest can rank a feature by dopamine release. Don't use neuroscience language as evidence of game-specific performance or as a target for engineering compulsive play.

## Deliver the work

Report the actual change or finding, supporting evidence, the test or experiment performed, and the unresolved limit. For a substantial review, a compact HTML report with annotated frames, an event diagram, and a short priority table is useful. For a small implementation change, a concise result and validation summary is enough.

State whether a claim is observed in the game, calculated from data, supported by external research, or still a design hypothesis. Distinguish a passing implementation check from measured player or commercial outcomes.

This skill doesn't authorize live wagering, paid generation, production deployment, or publication. Complete local work within the user's request and use the relevant authorization at the actual external action boundary.
