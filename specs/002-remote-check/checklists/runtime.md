# Runtime Requirements Checklist: Check the lab on every change

**Purpose**: Requirements-quality review for recreating functions on two CPUs
**Created**: 2026-11-15
**Feature**: [spec.md](../spec.md)

**Note**: This checklist tests whether the requirements are written clearly. It does not test the running system. Items stay unchecked until a reviewer marks them.

## Requirement Completeness

- [ ] CHK001 Is it specified which machine's CPU a recreated function must be able to run on? [Completeness, Spec §FR-011]
- [ ] CHK002 Is the developer machine's existing CPU called out as unchanged? [Completeness, Spec §FR-011]

## Requirement Clarity

- [ ] CHK003 Is "executable" defined as a successful invocation during infrastructure recreation, not only as a created function? [Clarity, Spec §Edge Cases]
- [ ] CHK004 Can a reviewer tell the Mac outcome from the remote-check outcome without guessing a CPU name? [Clarity, Spec §Assumptions]

## Requirement Consistency

- [ ] CHK005 Does FR-003's "same declarations" stay compatible with FR-011's per-machine CPU, with no sentence that forces one CPU for both machines? [Consistency, Spec §FR-003, Spec §FR-011]
- [ ] CHK006 Does the check-run contract require the publisher invocation to finish, matching the edge case that a non-executable function fails the check? [Consistency, contracts/check-run.md]

## Acceptance Criteria Quality

- [ ] CHK007 Is a failed function invocation specified as a failed check rather than a skipped step? [Acceptance Criteria, Spec §Edge Cases]

## Scenario Coverage

- [ ] CHK008 Is the remote-machine case covered separately from the developer-machine case? [Coverage, Spec §Clarifications]

## Edge Case Coverage

- [ ] CHK009 Is the failure mode when the function binary cannot run on the check machine written as an edge case? [Edge Cases, Spec §Edge Cases]

## Dependencies & Assumptions

- [ ] CHK010 Is the assumption that this Mac already has a working CPU recorded, so the default is not left implicit? [Assumptions, Spec §Assumptions]
