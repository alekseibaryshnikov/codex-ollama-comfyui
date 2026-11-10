---
name: sdd-tdd
description: "Use spec-driven development and TDD when implementing features, fixing bugs, or changing code behavior. Maintain behavioral specifications in source comments and documented tests with requirement traceability. Also use for behavior-preserving refactors and reviews of this workflow. Skip prose-only work, generated files, and unrelated read-only questions."
---

# SDD with source contracts and TDD

Treat source comments as maintained specification artifacts and tests as executable acceptance evidence. SDD means spec-driven development. For every behavior you add or change, keep this chain reviewable:

**Requirement -> source contract -> documented test -> observed result.**

These requirements are mandatory while this skill applies. They govern the requested change, not an unsolicited rewrite of the repository. User instructions can override them; disclose any resulting workflow exception. A skill supplies instructions, not mechanical enforcement or permission to expand scope.

## Establish the specification

1. Read applicable repository instructions, existing specs, relevant source contracts, and nearby tests. Use the project's test runner and documentation conventions.
2. Identify the requested outcomes and constraints before changing executable production code. Reuse existing requirement IDs. Otherwise introduce stable, descriptive IDs such as `EXPORT-AC1`, unique within their owning feature. Keep IDs stable across moves and renames; never recycle one for unrelated behavior.
3. Write or update the contract comment at the source boundary that owns the behavior, before implementing that behavior. One contract can cover several functions. For a new boundary, start with a comment or docstring and only the minimal declaration needed to collect the test; don't implement the behavior yet.
4. Link to existing authoritative specs using repository-relative paths and criterion IDs. Comments state the local obligations and reasoning; external specs retain their authority. If no spec exists, the source contract is the local specification artifact. Don't create a parallel spec document unless the task or repository requires it.
5. Resolve contradictions against the user's requested behavior. Ask only when ambiguity materially changes the observable contract and cannot be resolved from the available evidence. Continue independent work while waiting; don't invent requirements to match the implementation.

## Source comments are documentation artifacts

Every added or changed behavioral obligation must have an owning contract comment or docstring. Document the following where relevant:

- Requirement IDs and observable outcomes, including meaningful negative and boundary cases.
- Preconditions, postconditions, and invariants.
- Errors, side effects, ordering, persistence, retries, or concurrency guarantees affected by the change.
- The domain reason for a surprising rule or design constraint, when known.
- A stable pointer to its test file, suite, or test name so the evidence can be found.

Use the language's native comment/docstring style. Keep one authoritative owner per rule and reference it elsewhere. Explain what must hold and why; don't narrate syntax or add a comment to every line or trivial helper. Test-location pointers are navigation, not assertions that tests passed. Don't put execution logs, transient status, or unverifiable guarantees in source comments.

Update contracts, tests, and implementation together whenever behavior changes. Correct stale comments in the touched area. For generated or vendored code, document the contract in the maintained source, generator, adapter, or owning module instead of editing generated output. Don't invent unknown domain rationale; distinguish a confirmed requirement from an assumption.

Read [references/examples.md](references/examples.md) when introducing a contract format or choosing how much test documentation to write. Adapt its examples to the repository rather than imposing a new annotation language.

## Run TDD for every behavior change

Work in small acceptance slices. A bug fix requires a regression test that reproduces the bug before the fix.

1. **Specify.** State the slice's criterion in its source contract and describe the scenario in its test.
2. **Red.** Write the smallest meaningful test first and run it against the unchanged behavior. Observe failure for the missing or incorrect outcome. Record the exact command, failing test, and relevant failure reason in your work notes or tool evidence before implementing the slice.
3. **Check the failure.** A syntax error, unrelated import error, unavailable service, or broken fixture does not establish red. Repair the setup and rerun. For a new API, a missing symbol can demonstrate the initial gap, but collect and run the intended behavioral test using a minimal declaration before implementing the behavior. An intentional not-implemented failure at that boundary is valid; an unrelated setup failure isn't. A test that already passes is coverage or characterization, not evidence that it drove a change. Investigate whether the requested behavior already exists or the test misses it.
4. **Green.** Implement only enough production behavior for the slice, then rerun the same test and observe it pass. Don't weaken assertions, skip tests, or alter the contract merely to make the run green.
5. **Refactor.** Improve structure with tests green, keeping contracts and test references accurate. Run affected tests again after refactoring.
6. **Repeat and integrate.** Cover remaining acceptance criteria and relevant failure and boundary scenarios. Run the affected suite and repository-required checks, including integration or end-to-end tests where the contract crosses those boundaries. Report local and CI results separately; don't claim CI ran without evidence.

Never implement a batch of behaviors first and add their tests afterward while calling it TDD. Never claim an unobserved red or green run. If implementation already exists, add useful coverage and accurately call it tests added afterward; a safe isolated comparison against the pre-change revision can establish regression evidence when available, but doesn't turn the original sequence into TDD.

If execution is unavailable, still prepare the source contract and test first, state the exact blocker and command, and mark TDD verification incomplete. Continue independent or reviewable preparation where useful, but don't claim the red gate was met. Obtain the missing execution capability or an explicit user override before implementing dependent production behavior. Time pressure alone isn't an exception.

## Tests must explain the specification

Every new or materially changed behavioral test must be understandable without reading the implementation. In its native test documentation, provide:

- **Traceability.** The criterion ID and owning contract location, directly or inherited from a clearly documented suite.
- **Scenario.** Given the meaningful starting state, when the action occurs, then the observable outcome.
- **Purpose.** The business rule, boundary, or regression protected. Explain non-obvious fixture values and why an edge case matters.
- **Evidence boundary.** For integration, system, or simulated tests, state what is exercised for real and what is replaced, including what the test cannot establish.

A descriptive test title can carry Given/When/Then or purpose; don't duplicate it mechanically. Put missing details in a short comment or docstring. Shared suite documentation can cover common setup and traceability; scenario-specific differences must stay visible. Parameterized cases need readable case names or IDs, especially at boundaries.

Assert observable outcomes and meaningful effects, not private implementation steps unless the step is itself a requirement. Derive expected values from the specification or an independent known example, never by copying the production algorithm. Mock external boundaries deliberately; a mock assertion doesn't prove real persistence, delivery, or integration. Keep tests deterministic using controlled clocks, randomness, and fixtures where needed. Test the behavior, not the presence of comments or IDs.

## Handle changes that don't introduce new behavior

- **Behavior-preserving refactor.** Run existing tests first. Add characterization tests before refactoring if meaningful coverage is missing. Those tests should pass on the original implementation; don't manufacture a red run. Keep contract comments and traceability current and rerun after the refactor.
- **Comments, formatting, or documentation only.** Check accuracy and relevant formatting/build requirements. Don't invent a behavior test or a red/green cycle for prose.
- **Review only.** Assess the contract-to-test chain and the available execution evidence. Don't modify code or assert historical TDD sequencing based only on the final diff.
- **Behavior in configuration or infrastructure.** Apply the same contract and test-first discipline at the maintained configuration or automation boundary, using an appropriate validation or integration harness. Don't use syntax validation as evidence for a runtime guarantee.

## Completion gate

Before calling the change complete, verify that every changed criterion maps to an owning source contract and a documented test with a meaningful assertion. All applicable checks must have evidence, and required red/green runs must have happened in order. Review for stale comments, broken test pointers, undocumented scenarios, and claims beyond the test's evidence boundary.

In the handoff, summarize the changed behavior and give a compact traceability mapping: criterion -> contract location -> test location -> result. Include actual red/green commands and results, or link to recorded evidence. State any unrun checks, accepted overrides, or blocked criteria clearly. For a small change, one short mapping is enough. Missing execution evidence means verification remains incomplete, even when the patch is ready for review.
