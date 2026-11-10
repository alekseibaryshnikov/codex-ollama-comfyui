# Evidence, repeat activity, and commercial metrics

Read this when a task involves popularity statistics, retention, LTV, dopamine, or causal claims about a mechanic. The historical examples explain reasoning traps; they aren't current benchmarks.

## Keep five questions separate

| Question | Relevant evidence | Common mistake |
|---|---|---|
| Are people exposed to the game? | Lobby placement, acquisition sources, campaign reach. | Calling exposure retention. |
| Do people play many rounds? | Bets and duration per session or active account, with distributions. | Treating faster or more expensive play as enjoyment. |
| Do people return? | Same-age acquisition cohorts, return-day rates, active-day distribution. | Treating monthly volume as returning users. |
| Does the game earn contribution? | Wagers, payouts, incentives, fees, revenue share, and attribution. | Treating recycled wagers as deposits or revenue. |
| Is lifetime value strong? | Cohort contribution over time and a stated forecast for unobserved future value. | Relabeling a period average as LTV. |

Define the population, period, timezone, operator coverage, currency conversion, mode mix, and account identity. An account on one operator isn't necessarily a distinct person. Deduplicate consistently. Base bets, full bonus prices, and actual charges must not share an ambiguous denominator.

For LTV, state whose contribution is measured: casino, provider, or another business. Explain allocation when players switch games. Observed contribution and forecast lifetime value are different outputs. Use confidence intervals or explicit uncertainty where the data permits; don't invent precision from one aggregate window.

## Useful calculations and limits

- `Mean bets per active account = period bets / period distinct active accounts`.
- `Mean active days per active account = sum(daily distinct active accounts) / period distinct active accounts`.
- `Average recorded wager = period turnover / period bets`.
- `Largest-day turnover share = largest daily turnover / period turnover`.

For active days, keep account identity stable across dates. A visit crossing the reporting boundary may count as two dates. The mean doesn't reveal the median, daily-play share, return probability, or distribution. Recent arrivals have less opportunity to return. Compare same-age cohorts before calling one game more retentive.

Define whether D7 means activity on the seventh day, within seven days, or on/after day seven. Use the same definition for variants. When evaluating a change, separate acquisition source, market, device, feature mode, and incentive exposure where they could alter the result.

Look for concentration before generalizing: largest days, top-account contribution, means versus medians, and mode pricing. If account-level data isn't available, state what the aggregates cannot distinguish. A decline in account count with increased turnover needn't mean either worse or better cohort retention.

## Historical reference snapshot

**Checked November 9, 2026. Reporting window October 10 through November 8, UTC.** Candy first appears October 14, leaving only 26 post-launch dates. These are examples of a dated snapshot, not permanent facts to quote as current.

| Measure | Waylanders Forge | Candy Swipe MatchWin |
|---|---:|---:|
| Turnover | $973,890,551 | $80,583,858 |
| Bets | 95,316,744 | 96,198,259 |
| Active accounts | 93,623 | 228,782 |
| Summed daily active accounts | 282,684 | 411,172 |
| Mean active days per active account | 3.02 | 1.80 |

Waylanders' October 16 turnover was $382,285,614, or 39.3% of its period total. Versus the preceding equal-length window, turnover rose 33.5%, bets fell 1.4%, accounts fell 8.1%, and average wager rose 35.4%. Larger average wagers explain the aggregate turnover increase; these figures don't identify the accounts or modes responsible or establish LTV.

Sources:

- [Waylanders official game page](https://studio.engine.io/insights/games/valkyrie/waylanders-forge?range=30d).
- [Candy Swipe official game page](https://studio.engine.io/insights/games/coreffect-interactive/candy-swipe?range=30d).
- [Waylanders public aggregate endpoint](https://studio.engine.io/api/insights/games/valkyrie/waylanders-forge?range=30d).
- [Candy public aggregate endpoint](https://studio.engine.io/api/insights/games/coreffect-interactive/candy-swipe?range=30d).
- [Engine metric definitions](https://studio.engine.io/insights/developers). At the check date, the API documented live games and real-money play, USD-normalized totals, and unique accounts per operator. Its breakdown included sweepstakes coins. API units vary by endpoint, so read the current definition before calculating.

These URLs are rolling windows. Reopen current sources when making current claims. Record response dates and window boundaries; use complete UTC days where the source specifies them. Check count sums and whole-dollar rounding before drawing conclusions. Public aggregate requests don't justify collecting private account data or running live wagers.

The Olympus recording reviewed in this work was **Gates of Olympus Super Scatter**, not the original. No comparable first-party cohort LTV dataset for that edition was found. Don't transfer statistics from another Olympus edition or merge a partial tracker sample with an operator-wide census.

[SlotCatalog's SlotRank methodology](https://slotcatalog.com/en/read/What-is-SlotRank) measures lobby exposure weighted by estimated traffic. It doesn't establish player return or LTV. A dedicated [Candy Swipe promotion](https://stake.com/promotions/promotion/candy-swipe-mania) was also observed in November 2026; recheck campaign terms before discussing current effects.

## What reward research supports

Keep external research separate from game-specific observations and experiments:

- [Schultz, Dayan and Montague, 1997](https://www.gatsby.ucl.ac.uk/~dayan/papers/sdm97.html) supports a reward-prediction account of dopamine signaling. It isn't a dopamine measurement of these games.
- [Linnet et al., 2012](https://pubmed.ncbi.nlm.nih.gov/22889563/) used PET with 18 participants with pathological gambling and 16 controls. Its uncertainty-related pattern was found in the gambling group, not healthy controls. Don't generalize this into a universal optimal reward schedule.
- [Losses disguised as wins, 940-participant study](https://pubmed.ncbi.nlm.nih.gov/38169673/) found greater overestimation of genuine wins when videos included celebrated partial returns. This measures perception in an experiment, not these titles' retention or LTV.
- [Spetch et al., 2020](https://pubmed.ncbi.nlm.nih.gov/32056323/) studied simulated-slot choices in 630 participants. Casino-associated cues affected preference and payout memory; effects of neutral best-payout sounds were inconsistent. More sound doesn't imply more retention.
- [Clark et al., 2009](https://pubmed.ncbi.nlm.nih.gov/19217383/) found increased desire to continue after near misses on participant-controlled trials, despite lower pleasantness. This was behavioral and fMRI evidence, not a dopamine measurement. [Pisklak et al., 2020](https://pubmed.ncbi.nlm.nih.gov/31522339/) failed to find a near-miss reinforcement effect under its procedures. Don't claim a universal effect or manufacture near misses.

The common hypothesis drawn from the recordings was **a visible result that can still improve**, supported by readable progression and recognizable feedback. No analysis established which feature releases the most dopamine. Continued play, arousal, enjoyment, and contribution are distinct outcomes.

## A focused experiment

State a falsifiable question, then choose the evidence that can answer it. For example, does staged multiplier collection improve payout comprehension compared with a single reveal?

Hold the outcome sequence, costs, instructions, and acquisition context constant where possible. Counterbalance presentation order for repeated exposure. Record comprehension, subjective enjoyment, and voluntary preference separately. An exploratory playtest can find confusion; a sufficiently powered randomized cohort test can estimate effects on return behavior. Neither can infer dopamine release without appropriate direct methods.

Avoid universal sample sizes and pass thresholds. Pick them for the decision, expected effect, variability, and consequence. Report what was actually run, what was simulated, and what remains unmeasured.
