---
description: "Task list for scale job workers with demand"
---

# Tasks: Scale job workers with demand

**Input**: Design documents from `/specs/001-keda-jobs/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: One unit test is included because plan.md asks for a Nest unit test of the publisher and the worker handler. Broader TDD was not requested.

**Organization**: Tasks are grouped by user story so each story can be implemented and tested on its own.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Nest application: `jobs/src/`
- Queues: `terraform/jobs.tf`
- Cluster manifests: `k8s/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create the Nest project files `jobs/package.json` and `jobs/tsconfig.json` with bun, NestJS 11, and `@aws-sdk/client-sqs`
- [x] T002 [P] Add `jobs/Dockerfile` using the bun image, with the API as the default command
- [x] T003 [P] Add `jobs/.dockerignore` so `node_modules` is not copied into the image

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Queue infrastructure and the shared job shape. No user story starts before this.

- [x] T004 Declare `demo-jobs` and `demo-jobs-dlq` in `terraform/jobs.tf` with visibility timeout 30 seconds and redrive `maxReceiveCount` 3
- [x] T005 Declare publisher and worker IAM policies in `terraform/jobs.tf`: send only on `demo-jobs`; receive, delete, and get attributes on `demo-jobs` and `demo-jobs-dlq`
- [x] T006 Export `jobs_queue_url` and `jobs_dlq_url` from `terraform/jobs.tf`
- [x] T007 Create the job shape helper in `jobs/src/job.ts` where `type` is a non-empty string (default `manual`) and `jobId` is a non-empty string

**Checkpoint**: Foundation ready. User stories can begin.

---

## Phase 3: User Story 1 - Submit one job (Priority: P1) MVP

**Goal**: An HTTP caller submits one job and receives the queue message id.

**Independent Test**: `POST /jobs` returns 201 and the message is visible on `demo-jobs`. The order pipeline is unchanged.

### Implementation for User Story 1

- [x] T008 [P] [US1] Add the unit test for job construction and failure marking in `jobs/test/job.test.ts`
- [x] T009 [US1] Implement queue publishing in `jobs/src/jobs.service.ts` using the local endpoint and `demo-jobs`
- [x] T010 [US1] Implement `GET /health` and `POST /jobs` in `jobs/src/jobs.controller.ts` per `specs/001-keda-jobs/contracts/jobs-api.md`
- [x] T011 [US1] Wire the HTTP process in `jobs/src/main.ts` and `jobs/src/jobs.module.ts`

**Checkpoint**: User Story 1 works against LocalStack from the host.

---

## Phase 4: User Story 2 - Workers follow the amount of work (Priority: P2)

**Goal**: Worker replicas scale from 0 to 5 with the visible depth of `demo-jobs`.

**Independent Test**: An empty queue has zero worker pods. Six waiting jobs can raise the count above one and never above five. Successful jobs leave the queue.

### Implementation for User Story 2

- [x] T012 [US2] Implement the long-poll loop in `jobs/src/worker.ts` and `jobs/src/worker-loop.ts`. A job whose `type` is `fail` throws and is not deleted.
- [x] T013 [P] [US2] Add the kind cluster config in `k8s/kind-config.yaml` with host port 3000 mapped to node port 30000
- [x] T014 [P] [US2] Add the namespace and local credential secret in `k8s/namespace.yaml`
- [x] T015 [US2] Add the API Deployment and Service in `k8s/api-deployment.yaml`
- [x] T016 [US2] Add the worker Deployment in `k8s/worker-deployment.yaml` and the KEDA ScaledObject in `k8s/scaledobject.yaml` (`queueLength` 5, min 0, max 5)

**Checkpoint**: User Stories 1 and 2 work on kind.

---

## Phase 5: User Story 3 - A schedule keeps adding work (Priority: P3)

**Goal**: Every minute a CronJob submits `{ "type": "scheduled" }` through the API.

**Independent Test**: After two minutes, the API log shows two scheduled acceptances.

### Implementation for User Story 3

- [x] T017 [US3] Add the every-minute CronJob in `k8s/cronjob.yaml` that POSTs to `http://jobs-api.jobs.svc.cluster.local:3000/jobs`

**Checkpoint**: All three stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Operator instructions and ignore rules

- [x] T018 [P] Document the jobs flow in `readme.md`
- [x] T019 Ignore `jobs/node_modules/` in `.gitignore`
- [x] T020 Run the unit test in `jobs/` and apply `terraform/jobs.tf`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Setup. Blocks all user stories
- **User Stories (Phase 3+)**: Depend on Foundational. P1 before P2 before P3 for this feature, because the worker and the cron call the API
- **Polish**: Depends on the desired stories

### User Story Dependencies

- **User Story 1 (P1)**: Starts after Foundational. No dependency on other stories
- **User Story 2 (P2)**: Starts after the API can publish, so it can be tested with real messages
- **User Story 3 (P3)**: Starts after the API Service exists

### Parallel Opportunities

- T002 and T003 can run together
- T008 can run beside T004
- T013 and T014 can run together

### Parallel Example: User Story 2

```bash
Task: "Add k8s/kind-config.yaml"
Task: "Add k8s/namespace.yaml"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2
2. Complete Phase 3
3. Validate `POST /jobs` against LocalStack before building the cluster

### Incremental Delivery

1. Setup and queues
2. API acceptance
3. Worker and KEDA
4. CronJob
5. Readme and tests

## Notes

- [P] tasks use different files
- [US1], [US2], and [US3] map to the three stories in spec.md
- The order pipeline files stay untouched
