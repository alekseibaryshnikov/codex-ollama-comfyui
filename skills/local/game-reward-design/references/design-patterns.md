# Reward patterns and acceptance checks

Use the pattern that fits the game's current problem. These are design choices to test, not a universal recipe for retention. Timings, counts, board sizes, and payout distributions belong to the actual product.

## A result that unfolds clearly

**Useful when** players miss why a payout changed, events happen at once, or a cascade feels like unrelated flashes.

Show the causal order: identify the match, remove the matching objects, refill, resolve eligible modifiers, then settle. Keep the running amount in a stable location. During an important change, reduce competing visual emphasis rather than making every layer louder.

Gates of Olympus Super Scatter provided a concrete example in the November 2026 review: a $0.80 tumble result, an existing 12x total, and qualifying 15x and 12x orbs resolved into $0.80 x 39 = $31.20. The useful principle is readable calculation, not those specific numbers or Greek mythology.

**Acceptance checks**

- A deterministic sequence produces the specified total once, in normal and skipped playback.
- A boost contributes only under its actual eligibility rules.
- The final amount remains readable after transient numbers disappear.
- A new player can explain what caused the result. A correct arithmetic test alone doesn't establish comprehension.

**Tradeoff** More reveal stages can add clarity and anticipation, but can also create dead time. Use the minimum stages needed to understand the event. Don't prolong a resolved loss to manufacture suspense.

## A bonus with visible memory

**Useful when** bonus rounds feel disconnected or the player can't tell whether progress matters.

Give the feature a readable persistent state, such as one running multiplier, symbol-specific values, or damage to reward-containing blocks. Show what changes it, what future event uses it, how long it lasts, and when it resets. For a new prototype, start with one progression rule. Preserve necessary existing rules when improving a released game.

The three reference examples differ:

| Game | State in the reviewed feature | Player question |
|---|---|---|
| Waylanders Forge, Wayfinder's Blessing | A random symbol becomes wild; hit symbol values can double during the bonus. | What can these stronger symbols do next? |
| Olympus Super Scatter | A running multiplier applies to qualifying bonus wins. | What will the next eligible win become? |
| Candy Swipe, Ice Bonus | Cracked ice and collected multipliers persist while moves run down. | Can this block be opened before the feature ends? |

These aren't claims of permanent account progression, guaranteed profit, or verified retention effects.

**Acceptance checks**

- An event updates the correct state exactly once.
- State survives the specified boundary and resets at the specified boundary.
- Restart or reconnect restores the authoritative state when persistence is supported.
- Remaining actions and progress can be read together.
- Players understand that a larger bonus value may still require an eligible event to pay.

**Tradeoff** More persistent values mean more explanation and more interactions to validate. A symbol bar, board grid, and global meter shouldn't all be introduced to solve one unclear bonus.

## A meaningful direct action

**Useful when** choosing or manipulating objects is part of the intended experience, and the player's role is too passive or unclear.

Candy Swipe's distinctive action is swapping neighboring candies. Familiar objects and a local gesture give the player something concrete to inspect and do. That does not, by itself, prove a mathematical advantage from choosing a swap.

Specify the actual control contract. Does the action change board state, immediate score, legal moves, outcome distribution, or only the presentation? Keep instructions consistent with the real contract. If input affects a remotely resolved round, preserve the existing authoritative protocol rather than inventing client-side financial logic.

**Acceptance checks**

- Valid actions produce the specified visible effect; invalid ones have understandable feedback.
- Rapid, repeated, canceled, and overlapping inputs cannot create duplicate moves or charges.
- The game handles its supported input methods and preserves access to rules and exit controls.
- Players can describe what their choice controls without inventing a skill advantage.

**Tradeoff** Input adds involvement, but also demands attention and creates more failure cases. Don't add a swipe, timing test, or minigame just to make an unrelated product appear interactive.

## Feedback proportional to the event

**Useful when** the game feels flat, routine rewards obscure important events, or celebrations disrupt the loop.

Reuse existing feedback layers and tiers. Give important events a distinct combination of visual emphasis, motion, and sound if sound has actually been reviewed. Keep totals and critical controls stable. Tune with actual playback and listening; screenshots don't validate sound quality, synchronization, or feel.

For paid play, judge the financial outcome against the charged action or purchased feature. The reviewed Candy Ice Bonus returned $68.80 after a $100 purchase while displaying an Epic Win celebration. This is evidence of celebratory presentation accompanying a negative purchase result, not proof of the player's reaction.

**Acceptance checks**

- Skipping or reducing feedback doesn't alter rewards, eligibility, or settlement.
- Routine and exceptional events remain distinguishable.
- Paid cost, return, and net result are understandable.
- Presentation doesn't imply a false outcome or block essential controls.

**Tradeoff** A memorable celebration may help recognition, but extra intensity and longer count-ups don't establish greater enjoyment or repeat play.

## How to choose between changes

For an existing game, fix incorrect results and unclear causes before adding progression or new modes. Use evidence such as misunderstood payouts, abandoned controls, long inactive animation spans, or a clear player request.

For a new game, articulate one hook and build a small playable loop that demonstrates it. Add one progression feature only when it strengthens that loop. Keep art, outcome logic, presentation, and experiment design separable enough to test a specific claim without rebuilding the game.
