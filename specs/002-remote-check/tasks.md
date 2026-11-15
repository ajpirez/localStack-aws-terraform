---
description: "Task list for check the lab on every change"
---

# Tasks: Check the lab on every change

**Input**: Design documents from `/specs/002-remote-check/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: The stack job is the check described in `contracts/check-run.md`. No separate test framework was requested.

**Organization**: Tasks follow the three user stories. The workflow file is shared, so later stories extend the same job.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)

## Phase 1: Setup

**Purpose**: Record where the check lives

- [x] T001 Create `specs/002-remote-check/` with spec, plan, research, data model, contract, and quickstart

---

## Phase 2: Foundational

**Purpose**: One start command for the Mac and the runner

- [x] T002 Teach `scripts/up` to keep `~/.docker/run/docker.sock` when it exists and to use `/var/run/docker.sock` otherwise, and to accept `LOCALSTACK_AUTH_TOKEN` from the environment
- [x] T003 Point the Lambda socket in `docker-compose.yml` at `${LAMBDA_DOCKER_SOCK}` with the Mac path as the default

**Checkpoint**: `./scripts/up` still starts LocalStack on this Mac.

---

## Phase 3: User Story 1 - A change is checked without the developer machine (Priority: P1)

**Goal**: A published change starts LocalStack, applies Terraform, and accepts `job-ci-1`.

**Independent Test**: A run with the secret accepts `job-ci-1`. A run without the secret fails. The token is not in a tracked file.

### Implementation for User Story 1

- [x] T004 [US1] Add the unit job and the stack job start (`./scripts/up`, `terraform apply`, image build, kind) in `.github/workflows/ci.yml`
- [x] T005 [US1] In `.github/workflows/ci.yml`, replace `192.168.65.254` with the LocalStack IP on the kind network and accept `job-ci-1` through `POST /jobs`
- [x] T009 [US1] Build the Lambda functions for the CPU of the machine running Terraform: default `arm64` in `terraform/provider.tf` and `terraform/lambda.tf`, and `TF_VAR_lambda_architecture=x86_64` in `.github/workflows/ci.yml`

**Checkpoint**: User Story 1 is the stack job through the acceptance call.

---

## Phase 4: User Story 2 - The worker and the schedule are part of the same check (Priority: P2)

**Goal**: The worker log contains `job-ci-1` and one schedule run completes.

**Independent Test**: The stack job fails unless both the worker log and `job/ci-schedule` succeed.

### Implementation for User Story 2

- [x] T006 [US2] In `.github/workflows/ci.yml`, wait for a worker log containing `job-ci-1` and complete one Job created from `jobs-schedule`

**Checkpoint**: User Stories 1 and 2 pass in the same stack job.

---

## Phase 5: User Story 3 - The worker bound is still five (Priority: P3)

**Goal**: The check reads a maximum of five workers.

**Independent Test**: The stack job fails if `maxReplicaCount` is not 5.

### Implementation for User Story 3

- [x] T007 [US3] In `.github/workflows/ci.yml`, assert `scaledobject/jobs-worker` `maxReplicaCount` is 5

**Checkpoint**: All three stories are covered by the workflow.

---

## Phase 6: Polish

**Purpose**: Tell the maintainer how to supply the token

- [x] T008 Document the Actions secret and `./scripts/up` behavior in `readme.md` and `specs/002-remote-check/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup**: No dependencies
- **Foundational**: Depends on Setup. Blocks the workflow, because the runner must call `./scripts/up`
- **User Stories**: Depend on Foundational. US2 and US3 extend the stack job started in US1
- **Polish**: Depends on the workflow existing

### User Story Dependencies

- **User Story 1 (P1)**: Starts after Foundational
- **User Story 2 (P2)**: Starts after the acceptance call exists
- **User Story 3 (P3)**: Starts after the ScaledObject is applied

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2
2. Complete the stack job through `POST /jobs`
3. Add the worker log, the schedule run, and the bound of five

## Notes

- [US1], [US2], and [US3] map to the stories in spec.md
- The check does not pause the worker to force five pods
