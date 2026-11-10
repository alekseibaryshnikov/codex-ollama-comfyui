---
name: stake-submission-review
description: Review a Stake Engine game against a supplied 51-point submission and release checklist. Use for pre-upload approval checks, RGS and frontend readiness, Social Mode compliance, replay support, or final release sign-off.
---

# Stake submission review

Review the game against [the full checklist](references/checklist.md). Read all 51 rows before assessing readiness; use their `SE-01` through `SE-51` IDs in findings and evidence.

## Source and scope

The reference preserves the user's Stake reviewer checklist supplied on 9 November 2026. Its original capture date and version are unknown. It is a baseline, not a claim that Stake's requirements are frozen or identical for every team. When the user supplies a newer checklist or their authenticated team checklist, compare it with this baseline and use that applicable source for the review. State any differences. If current verification is unavailable, say which snapshot was used.

This package is self-contained. Base requirements on the applicable checklist and specifications, rather than unverified thresholds, example bet limits, legal text, review timings, or rating rules. The supplied checklist includes a thumbnail check and final Math approval; it does not define a complete artwork standard or math certification procedure.

## Review workflow

1. Identify the build/version, available modes, target platforms, and whether Social Mode applies. Inspect the relevant source, existing tests, build artifacts, and available runtime. Run the checks the available environment can actually support.
2. Assess every applicable pre-submission row, `SE-01` through `SE-44`. Keep later release sign-off, `SE-45` through `SE-51`, separate. Missing approval notifications before submission are pending release work, not evidence of a defective build.
3. Assign each row **Pass**, **Fail**, **Unverified**, or **N/A**. A Pass needs relevant evidence. A Fail needs an observed mismatch. Use Unverified when access, a specification, hardware, or execution is missing. Use N/A only with a concrete reason, such as a confirmed absent optional feature. Social checks are N/A only when that jurisdiction is outside the requested submission scope.
4. Record file/line locations, actual commands and outcomes, network observations, screenshots, or platform records as appropriate. A source review or mocked request does not establish real RGS behavior. Desktop emulation does not establish performance on older mobile hardware. One successful base-mode spin does not cover other modes, replay, or Social Mode.
5. Report observed blockers first, followed by a compact ID/status/evidence/action table and remaining release tasks. Prefer a readable HTML report when useful. Claim pre-submission readiness only when every applicable pre-submission row passes. Claim final sign-off only when all applicable release rows also pass. Neither result guarantees Stake approval or replaces a separate required math review.

## Requirements that need another specification

The supplied rows refer to artwork guidelines, restricted title terms, required social translations, Social Mode names, a general disclaimer, and high-cost mode confirmation without including their full definitions. Obtain the applicable current team/official material before passing those details. If it is unavailable, mark the affected check Unverified and explain exactly what is missing. Do not invent a translation list, disclaimer, numeric cost threshold, currency precision rule, or device support floor.

Use authenticate-provided betting parameters and active-round amounts as required by the checklist; fixed USD/JPY/MXN examples are not substitutes. Keep its zero-win end-round rule separate from insufficient-balance play prevention. Check sub-cent payouts without silently rounding a real payout to zero.

The source calls for five wins per game mode, Popout S/L for the game, and Popout S for replays. Keep those distinct. Extra samples are optional reviewer choices, not additional Stake requirements. Apply the English-only Social Mode rule alongside the general requirement that invalid language parameters do not break the display.

Read release-platform and notification state when assessing final sign-off. This checklist is not authorization to upload a build, change platform settings, publish a game, or send channel messages. Perform those actions only within the user's requested scope.
