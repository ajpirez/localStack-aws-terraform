# Feature Specification: Check the lab on every change

**Feature Branch**: `002-remote-check`

**Created**: 2026-11-14

**Status**: Draft

**Input**: User description: "Cada cambio debe probarse solo, fuera de esta Mac, con el mismo circuito: cola, aceptación de un trabajo, un worker que lo registra, el horario que publica uno, y el límite de workers. El token no se guarda en el repositorio. El laboratorio local no cambia."

## Clarifications

### Session 2026-11-15

- Q: When the check recreates the existing functions, which CPU must be able to run them? → A: The CPU of the machine running the check. This Mac keeps the CPU it already uses.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A change is checked without the developer machine (Priority: P1)

A maintainer publishes a change. A fresh check starts on its own, accepts one job, and reports pass or fail.

**Why this priority**: Without an automatic pass or fail, the maintainer still has to repeat the lab by hand.

**Independent Test**: Publish a change that does not touch the developer machine and read a single pass or fail for one accepted job.

**Acceptance Scenarios**:

1. **Given** the access token is available to the check and not stored in the project files, **When** a change is published, **Then** the check starts a clean local environment, accepts one job with a known identifier, and reports pass within 40 minutes.
2. **Given** the access token is missing, **When** a change is published, **Then** the check fails and the token is still absent from the project files.
3. **Given** the developer starts the lab on this Mac, **When** they use the existing start command, **Then** that command still reaches the local environment through the Mac socket.

---

### User Story 2 - The worker and the schedule are part of the same check (Priority: P2)

The check shows that a worker recorded the accepted job and that the schedule path also submits one job through the same acceptance path.

**Why this priority**: Acceptance alone does not show that work is consumed or that the schedule still reaches the same path.

**Independent Test**: After one accepted job, read the worker record for that identifier, then run the schedule once and confirm a second acceptance.

**Acceptance Scenarios**:

1. **Given** a job was accepted by the check, **When** a worker runs, **Then** the worker record contains that job's identifier and the job is no longer waiting.
2. **Given** the schedule is installed, **When** the check runs that schedule once, **Then** one scheduled submission is accepted through the same path as a manual submission.

---

### User Story 3 - The worker bound is still five (Priority: P3)

The check confirms the agreed capacity: no workers while idle is the resting state, and the upper bound stays five.

**Why this priority**: The demand rule is already specified. The check must not silently change it.

**Independent Test**: Read the configured upper bound and observe that a single waiting job brings up a worker.

**Acceptance Scenarios**:

1. **Given** the check has installed the worker rule, **When** the bound is read, **Then** the maximum number of workers is five.
2. **Given** one job is waiting, **When** the check looks for workers, **Then** at least one worker is running.

### Edge Cases

- The check starts from an empty environment. Resources from a previous check are not reused.
- A failed schedule submission is reported as a failed check, not as an acceptance.
- The existing order pipeline is still present after the infrastructure is recreated.
- The developer machine keeps its current socket path. The remote machine uses its own socket only when the Mac socket is absent.
- Recreating a function on a machine whose CPU cannot run it fails the check. The function must be executable on that machine. This Mac keeps its current CPU.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A published change MUST start a check without anyone running commands on the developer machine.
- **FR-002**: The check MUST use only the local stand-in for AWS, in region `us-east-1`, with the test credentials. It MUST NOT call real AWS.
- **FR-003**: The check MUST recreate the declared infrastructure, including the work queue and the existing order pipeline, from the same declarations used on the developer machine.
- **FR-011**: A recreated function MUST be executable on the CPU of the machine running the check. On this Mac the functions MUST keep the CPU they already use.
- **FR-004**: The check MUST accept one job with a known identifier and MUST show that identifier in the worker record.
- **FR-005**: The check MUST run the schedule path once and MUST show that submission as accepted.
- **FR-006**: The check MUST confirm the worker upper bound is five and MUST observe at least one worker for a waiting job.
- **FR-007**: The access token MUST be supplied from outside the project files and MUST NOT be written into the repository.
- **FR-008**: Starting the lab on this Mac MUST keep using the existing start command and the Mac socket.
- **FR-009**: A missing token MUST fail the check.
- **FR-010**: The check MUST finish with a single pass or fail within 40 minutes.

### Key Entities

- **Check run**: One automatic pass or fail for a published change. It starts from an empty environment and does not keep data afterward.
- **Accepted job**: A submission with a known identifier, accepted through the same path a person uses, then recorded by a worker.
- **Scheduled submission**: One submission produced by the schedule path, accepted the same way as an accepted job.
- **Access token**: The secret that allows the local stand-in to start. It lives outside the project files.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A maintainer can tell pass from fail for a published change without using the developer machine.
- **SC-002**: A passing check accepts one known job and a worker records that same identifier.
- **SC-003**: A passing check accepts one scheduled submission through the same path.
- **SC-004**: A passing check reports an upper bound of five workers.
- **SC-005**: The check reports pass or fail within 40 minutes.
- **SC-006**: Searching the project files does not reveal the access token.

## Assumptions

- The check runs on a clean machine provided for that run and discards the machine at the end.
- The local lab on the developer Mac stays as it is, including the start command and the Mac socket.
- The hosting service stores the access token and injects it only for the check.
- One waiting job is enough to prove a worker appears. Filling the queue until five workers are visible stays a manual demonstration, not part of this check.
- The order pipeline is recreated by the same declarations and is not redesigned.
- This Mac already runs those functions on its own CPU. The remote check uses the CPU of its own machine. The declarations stay one set; only the CPU setting changes with the machine.
