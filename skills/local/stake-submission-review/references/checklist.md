# Supplied Stake reviewer checklist

## Provenance and use

Source: the 51 checkbox labels in the Stake review UI HTML supplied by the user on **9 November 2026**. The original source capture date, checklist revision, and account/team scope were not supplied. This is a maintained transcription of that snapshot, not an independently verified universal Stake policy.

Requirement labels below preserve the source wording, including spelling. `SE-01` through `SE-51`, grouping labels, phase separation, and the evidence suggestions are local review aids. Evidence suggestions explain how to assess a requirement; they are not additional Stake rules or claims that a check has run.

Rows `SE-01` through `SE-44` are pre-submission checks. Rows `SE-45` through `SE-51` are operational sign-off checks from the source's final section; collect them at the appropriate approval/release stage. Optional-feature and jurisdiction checks may be N/A only with a reason.

Public starting points for checking updates or obtaining missing specifications:

- [Approval Guidelines](https://stake-engine.com/docs/approval-guidelines)
- [Submission Checklist](https://stake-engine.com/docs/approval-guidelines/submission-checklist)

The detailed checklist may require an authenticated account and may vary by team. Obtain the applicable current specifications for artwork, restricted terms, social translations/names, and disclaimer wording before passing those checks. The pasted source does not contain them. It also does not define a high-cost threshold or full math approval procedure.

Record each result as **Pass**, **Fail**, **Unverified**, or **N/A**, with the observed evidence and its limits. Never pre-check these rows merely because this reference exists.

## PreChecks

| ID | Supplied requirement | Evidence to collect |
| --- | --- | --- |
| SE-01 | Game authenticates with RGS sucessfully on game launch | Launch a valid session and observe successful RGS authentication. |
| SE-02 | Game authentication fails correctly with an invalid rgs_url | Launch with an invalid rgs_url. Observe failed authentication and usable error handling; the game must not appear authenticated. |
| SE-03 | Clicking on the bet button sends a successful play request to RGS | Click the bet button in an authenticated funded session and observe a successful RGS play request. |

## Loader restriction

| ID | Supplied requirement | Evidence to collect |
| --- | --- | --- |
| SE-04 | Game should not contain the Stake Engine Loader | Inspect the shipped build and launch experience for the Stake Engine Loader. |

## Compliance Checks

| ID | Supplied requirement | Evidence to collect |
| --- | --- | --- |
| SE-05 | Game title is unique and does not use restricted terms | Compare the title with existing titles and the applicable restricted-terms rules. Obtain the current restrictions if unavailable. |
| SE-06 | Game assets and imagery do not contain offensive or inappropriate content | Inspect the shipped symbols, artwork, animation, and other imagery against applicable content guidance. |
| SE-07 | Game is sufficiently distinct from existing titles and series | Compare the game design, presentation, and title/series identity with existing titles; document the comparison. |

## Game Thumbnail

| ID | Supplied requirement | Evidence to collect |
| --- | --- | --- |
| SE-08 | Game thumbnail meets Stake artwork guidelines | Inspect the submitted thumbnail against the applicable Stake artwork specification. The pasted source does not supply that specification. |

## RGS / Bet Levels

| ID | Supplied requirement | Evidence to collect |
| --- | --- | --- |
| SE-09 | Game dynamically uses all betting parameters from the authenticate response | Use session/config variations to verify all returned betting parameters drive selection and validation. Fixed currency examples are insufficient. |
| SE-10 | Active rounds restore the bet amount from the authenticate response | Reload an active round and compare the restored bet with the active-round amount in authenticate, including when the default differs. |

## RGS / Currency Support

| ID | Supplied requirement | Evidence to collect |
| --- | --- | --- |
| SE-11 | Game supports and displays currencies correctly | Exercise supported currency sessions and inspect amounts and currency labels against the applicable currency definitions. |
| SE-12 | Game displays sub-cent payouts correctly | Exercise a non-zero payout below one cent. Compare the display with the actual server amount and applicable currency precision; do not silently display zero. |

## RGS / Requests

| ID | Supplied requirement | Evidence to collect |
| --- | --- | --- |
| SE-13 | Zero-win bets do not send an end-round request to the RGS | Observe real network traffic for a zero-win bet and verify no end-round request is sent. |
| SE-14 | Insufficient balance bets do not send a play request to the RGS | With balance below the selected cost, attempt a bet and verify no RGS play request is sent. |

## Frontend / Controls and frame

| ID | Supplied requirement | Evidence to collect |
| --- | --- | --- |
| SE-15 | Space bar should be bound to the bet button | Use Space with normal gameplay focus and verify the bet action works without duplicate bets. |
| SE-16 | Main game frame should not be scrollable | Check the main game frame at target viewports for unintended scrolling. Intentional scrolling inside information panels is a separate concern. |

## Frontend / Game Rules

| ID | Supplied requirement | Evidence to collect |
| --- | --- | --- |
| SE-17 | RTP and Max Win are clearly stated within the game rules | Open rules and compare stated RTP and Max Win with the applicable game/mode definitions. |
| SE-18 | Payout information per symbol must be clearly communicated | Inspect symbol payout information for clarity and consistency with the game definitions. |
| SE-19 | Win combinations are displayed in the game rules | Inspect the winning combination definitions and compare them with implemented payout patterns. |
| SE-20 | Game modes include description and cost information | Inspect each available mode for a description and its cost. |
| SE-21 | Free game and re-trigger conditions are clearly displayed in the game rules | Inspect free-game trigger and re-trigger conditions and compare them with game behavior; explain N/A if those features are absent. |
| SE-22 | General disclaimer is included in the game information | Locate the disclaimer in game information and compare it with the applicable required wording. The source does not include the full disclaimer. |
| SE-23 | High cost bet modes require confirmation before activation | For applicable high-cost modes, attempt activation and verify confirmation before committing. Obtain the applicable threshold; do not invent one. |

## Frontend / Responsive Checks

| ID | Supplied requirement | Evidence to collect |
| --- | --- | --- |
| SE-24 | Game functions correctly on Desktop/Laptop | Exercise the game and controls on the target desktop/laptop environments. |
| SE-25 | Game functions correctly on Popout S/L | Exercise gameplay and controls in both Popout S and Popout L. |
| SE-26 | Game functions correctly on Mobile | Exercise the game and controls on target mobile devices and orientations. |
| SE-27 | Double tap to zoom is disabled on mobile | Double-tap the mobile game surface and verify zoom does not activate. Do not expand this into an unsupported requirement to disable all browser zoom. |

## Frontend / Auto Play and interaction guide

| ID | Supplied requirement | Evidence to collect |
| --- | --- | --- |
| SE-28 | Auto-bet requires a confirmation step before starting | Attempt to start autoplay and verify a confirmation step occurs before consecutive plays begin; explain N/A if autoplay is absent. |
| SE-29 | User interaction guide is included in the game information | Open game information and verify it explains user controls and interactions. |

## Frontend / Sounds and music

| ID | Supplied requirement | Evidence to collect |
| --- | --- | --- |
| SE-30 | Game provides an option to disable sounds | Disable sounds using the game control and verify audible output follows that setting. |

## Frontend / Language support

| ID | Supplied requirement | Evidence to collect |
| --- | --- | --- |
| SE-31 | Game supports English language | Launch in English and verify readable, usable game text. |
| SE-32 | Invalid language parameters do not break game display | Launch with an invalid language parameter and verify the game remains readable and usable. |

## Payout sample and Mystery Mode

| ID | Supplied requirement | Evidence to collect |
| --- | --- | --- |
| SE-33 | Check 5 wins for each game mode against the Game Rules | For each available game mode, observe five winning outcomes and compare their displayed payouts with the rules and authoritative outcome amounts. Record the outcomes and sample limits. |
| SE-34 | If Mystery Mode is present in the game, any numerical values representing chances or probabilities are accurate | If Mystery Mode exists, independently compare every displayed numerical chance or probability with the implemented authoritative distribution. Otherwise document N/A. |

## Jurisdiction / Stake.US

| ID | Supplied requirement | Evidence to collect |
| --- | --- | --- |
| SE-35 | Is the game compliant with the required translations for a social game? | Compare Social Mode text with the required social translation guidance, including rules, controls, popups, and errors. Obtain the current glossary if unavailable. |
| SE-36 | Game supports SC and GC currencies & values do not display a "$" prefix | Exercise SC and GC sessions and verify their displayed values do not use a dollar prefix. |
| SE-37 | Game mode naming follows Social Mode terminology guidelines | Compare every Social Mode name with the applicable Social Mode terminology guidance. Obtain that guidance if unavailable. |
| SE-38 | Replay window does not contain restricted words | Inspect the Social Mode replay window against the required restricted-word list. |
| SE-39 | English is the only supported language in Social Mode | Try English and non-English language parameters in Social Mode and verify only English is supported without breaking display. |

## Replay Support

| ID | Supplied requirement | Evidence to collect |
| --- | --- | --- |
| SE-40 | Supports replay urls, loads and plays desired event | Open a replay URL and verify it loads and plays the requested event. |
| SE-41 | Supports all optional parameters like, currency, language, amount | Exercise replay currency, language, and amount parameters and any other optional parameters in the applicable replay specification. |
| SE-42 | Replay allows replaying the event again after completion | Finish a replay and verify the same event can be played again. |
| SE-43 | UI clearly displays bet cost and applied multiplier | Compare replay cost and applied multiplier with the requested event and actual mode cost. |
| SE-44 | Supports Replays in Popout S view | Complete and repeat a replay in Popout S; inspect its controls and cost display. |

## Final approval and release sign-off

| ID | Supplied requirement | Evidence to collect |
| --- | --- | --- |
| SE-45 | Game has bet-level templates applied | Inspect the target game configuration for applied bet-level templates. |
| SE-46 | Provably Fair and Replay are enabled | Inspect platform configuration and verify both Provably Fair and Replay are enabled. A working replay URL alone is insufficient. |
| SE-47 | Front and Math requests are approved | Inspect the specific Front and Math request versions and verify both are approved. |
| SE-48 | Game is posted in the stake-engine-game-approved channel | Locate the game notification in stake-engine-game-approved. Observing this record does not authorize posting a message. |
| SE-49 | Game works correctly on older mobile devices (Android and IOS) | Exercise the game on older Android and iOS hardware in the applicable support range and record models/OS versions. Emulation alone leaves this check unverified. |
| SE-50 | Approval requests is closed after the game is live & emoji's are added to slack notification | After live status, verify the approval request is closed and the required notification markers are present. The source does not specify exact emoji values. |
| SE-51 | Game Released | Verify actual released/live status for the intended game and version; distinguish it from approval or upload completion. |
