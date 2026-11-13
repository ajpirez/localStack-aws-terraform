# Feature Specification: Scale job workers with demand

**Feature Branch**: `001-keda-jobs`

**Created**: 2026-11-13

**Status**: Draft

**Input**: User description: "Crear una cola nueva, un API que publica un trabajo al llamarlo, suscriptores que se levantan según la demanda y un cron que publica un trabajo cada minuto. El circuito actual de pedidos no se toca."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Submit one job (Priority: P1)

An operator sends one job and receives confirmation that it was accepted and is waiting to be worked.

**Why this priority**: Without a way to add work, nothing else in the feature has a purpose.

**Independent Test**: Send one job with a recognizable identifier and confirm it is waiting, untouched by the existing order pipeline.

**Acceptance Scenarios**:

1. **Given** the local environment is running and the new work queue is empty, **When** the operator submits a job, **Then** the system accepts it and the job is waiting in the new work queue within 5 seconds.
2. **Given** a job was accepted, **When** the operator looks at the existing order pipeline, **Then** that pipeline has no new order from this submission.

---

### User Story 2 - Workers follow the amount of work (Priority: P2)

When work is waiting, workers appear and process it. When the queue is idle, no worker stays running.

**Why this priority**: The reason for the feature is to spend capacity only while there is demand.

**Independent Test**: Place several jobs, observe workers start and finish them, then observe that no worker remains once the queue is empty.

**Acceptance Scenarios**:

1. **Given** no jobs are waiting, **When** an observer checks running workers, **Then** zero workers are running.
2. **Given** more jobs are waiting than one worker should take, **When** demand stays above that threshold, **Then** more than one worker is running and the count does not exceed five.
3. **Given** workers are running, **When** they finish the waiting jobs, **Then** the work queue is empty and the worker count returns to zero.
4. **Given** a worker finishes a job successfully, **When** the job is checked again, **Then** it is no longer waiting.

---

### User Story 3 - A schedule keeps adding work (Priority: P3)

Once a minute, without a person, the system submits one additional job through the same acceptance path used by an operator.

**Why this priority**: It proves the acceptance path stays available and creates visible demand over time.

**Independent Test**: Leave the system idle for two minutes and confirm two new scheduled jobs were accepted.

**Acceptance Scenarios**:

1. **Given** the schedule is active, **When** one minute passes, **Then** one new job is accepted through the same path an operator uses.
2. **Given** a scheduled submission cannot be accepted, **When** the minute passes, **Then** the failure is visible in the schedule's record and the existing order pipeline is unchanged.

---

### Edge Cases

- A job that cannot be completed is returned and tried again. After three unsuccessful attempts it leaves the work queue and waits in a failed-job holding area.
- Two submissions with different identifiers both remain waiting until a worker takes each one.
- Submitting a job while the local environment is down is rejected with a visible error. Nothing is reported as accepted.
- The existing order pipeline keeps its current topics, queues, and functions. This feature does not add orders there.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST accept a single job submission and confirm acceptance to the caller.
- **FR-002**: An accepted job MUST wait in a new work queue that is separate from the existing order pipeline.
- **FR-003**: The system MUST show whether the acceptance service is alive.
- **FR-004**: While no jobs are waiting, the system MUST run zero workers for this queue.
- **FR-005**: The system MUST start additional workers as waiting jobs grow, and MUST NOT run more than five workers for this queue.
- **FR-006**: One worker MUST be enough for up to five waiting jobs. A sixth waiting job MUST be able to justify a second worker.
- **FR-007**: A worker MUST record each job it takes and MUST remove that job from the work queue only after successful completion.
- **FR-008**: A job that fails three times MUST leave the work queue and MUST be available in a failed-job holding area.
- **FR-009**: Once a minute the system MUST submit one job through the same acceptance path an operator uses.
- **FR-010**: A failed scheduled submission MUST be visible to an operator and MUST NOT be reported as accepted.
- **FR-011**: This feature MUST NOT create, change, or delete resources in the existing order pipeline.

### Key Entities

- **Job**: A unit of work with a type and an identifier. It is accepted, waiting, in progress, completed, or failed.
- **Work queue**: Holds accepted jobs until a worker takes them. Separate from the order pipeline.
- **Failed-job holding area**: Holds a job after three unsuccessful attempts.
- **Worker**: A short-lived processor. Its count follows how many jobs are waiting, from zero to five.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An operator receives confirmation of an accepted job within 5 seconds.
- **SC-002**: With an empty work queue, an observer finds zero workers for that queue.
- **SC-003**: With at least six jobs waiting, more than one worker is running, and the count never exceeds five.
- **SC-004**: After workers finish a batch, the work queue has no remaining accepted jobs and the worker count is back to zero within 2 minutes.
- **SC-005**: Over two undisturbed minutes, two scheduled jobs are accepted.
- **SC-006**: A job that fails three times is absent from the work queue and present in the failed-job holding area.
- **SC-007**: After using this feature, the existing order pipeline has the same topics, queues, and functions as before.

## Assumptions

- The local cloud emulator is already running on this machine. This feature does not replace it.
- Operators call the acceptance path over HTTP on the local cluster.
- Workers and the acceptance service run inside a local cluster on the same machine and reach the emulator from there.
- Scheduled submission uses a one-minute cadence.
- A worker handles up to five waiting jobs before another worker is justified.
- The maximum number of workers for this queue is five.
- Failed jobs are retried up to three times, matching the rule already used for orders.
- The first version does not require a person to sign in.
- The existing order pipeline stays unchanged.
