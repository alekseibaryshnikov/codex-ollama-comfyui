# Contract and test examples

Use the repository's own language and test conventions. The labels here are examples, not required syntax. Keep the behavioral content and traceability.

## A source contract

Suppose the user requires a fixed one-hour session lifetime, with expiration at the exact cutoff. An owning Python function can carry this contract:

```python
def session_expired(issued_at: int, now: int) -> bool:
    """Decide expiry for a fixed one-hour session.

    SESSION-AC1: Return False before issued_at + 3600.
    SESSION-AC2: Return True at or after issued_at + 3600.
    Preconditions: inputs are UTC epoch seconds from a trusted clock;
        now >= issued_at. Caller validates these conditions.
    Invariant: this decision never extends a session or changes stored state.
    Reason: the session policy grants exactly one hour, without a grace period.
    Evidence: tests/test_session.py::SessionExpiryTests (SESSION-AC1, SESSION-AC2).
    """
    return now >= issued_at + 3600
```

Write that contract before the implementation. To start the new API, a temporary
`raise NotImplementedError` body is enough to collect a behavioral test. It is a
declaration scaffold, not a completed behavior. Add one scenario, observe it fail,
implement the slice, then add the next scenario and repeat.

If a repository spec already defines the lifetime, reference its path and
criterion here. Don't add an alternative policy in a comment. The precondition
is explicit: this example does not specify rejection of untrusted or backwards
timestamps. Don't invent such behavior or claim these tests verify it.

## Documented behavioral tests

The following is the final test suite after incremental TDD, not an instruction
to paste the complete implementation before writing tests:

```python
import unittest

from session import session_expired


class SessionExpiryTests(unittest.TestCase):
    """Contract: session.py::session_expired, SESSION-AC1 and SESSION-AC2.

    Pure policy tests use explicit UTC seconds. They don't establish that a
    live HTTP endpoint rejects an expired session or uses a trusted clock.
    """

    def test_session_remains_valid_one_second_before_cutoff(self):
        """SESSION-AC1: Given issuance at 100, when now is 3699, stay valid.

        This protects the final permitted second from premature expiration.
        """
        self.assertFalse(session_expired(issued_at=100, now=3699))

    def test_session_expires_at_and_after_cutoff(self):
        """SESSION-AC2: Given issuance at 100, expire at 3700 and later.

        The exact-cutoff case protects the inclusive policy boundary;
        the later case prevents accidental equality-only expiration.
        """
        for case_name, current_time in [("exact_cutoff", 3700), ("after_cutoff", 3701)]:
            with self.subTest(case=case_name):
                self.assertTrue(session_expired(issued_at=100, now=current_time))
```

For an existing `now > issued_at + 3600` bug, write and run the exact-cutoff
regression first. Expect a failed `assertTrue` for `now=3700`, then fix the
comparison and rerun. Don't claim that failure unless you actually observed it.

## What adds no specification value

Avoid `# Check expiry`, `# Call function`, or `# Assert result`. They explain
syntax but leave the intended rule unclear. Avoid tests that check comment
strings, number of documentation fields, or calls to private helpers. Those
don't establish the session policy.

## Compact evidence for a handoff

After actually executing the commands, a handoff could say:

```text
SESSION-AC2 -> session.py::session_expired
            -> tests/test_session.py::SessionExpiryTests.test_session_expires_at_and_after_cutoff
Red:   python -m unittest discover -s tests -p test_session.py
       Exact-cutoff assertion failed on the old strict comparison.
Green: same command, both tests passed after the inclusive comparison fix.
Scope: pure policy tests; live endpoint enforcement wasn't exercised.
```

For multiple criteria, use a short table. Keep logs in test output or work notes,
not in source contracts. Report only evidence from the actual task.
