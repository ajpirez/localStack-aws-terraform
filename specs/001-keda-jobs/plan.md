# Implementation Plan: Scale job workers with demand

**Branch**: `001-keda-jobs` | **Date**: 2026-11-13 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-keda-jobs/spec.md`

## Summary

An operator submits one job and a minute schedule submits another through the same HTTP path. Both land on a new LocalStack queue, `demo-jobs`. A Nest worker deployment in a local kind cluster consumes that queue. KEDA scales it from 0 to 5 replicas, one replica per five visible messages. Jobs that fail three times move to `demo-jobs-dlq`. The existing order pipeline stays unchanged.

## Technical Context

**Language/Version**: TypeScript on Node 22, NestJS 11, installed with bun

**Primary Dependencies**: `@aws-sdk/client-sqs`, Kubernetes kind, KEDA `aws-sqs-queue` scaler, Helm

**Storage**: SQS queues `demo-jobs` and `demo-jobs-dlq` in LocalStack. No database.

**Testing**: Nest unit test for the publisher and the worker handler. End-to-end steps in `quickstart.md`.

**Target Platform**: Docker Desktop on macOS. LocalStack on the host. Workloads inside a one-node kind cluster.

**Project Type**: Web service plus a queue worker, deployed to local Kubernetes

**Performance Goals**: Accept a job within 5 seconds. Return to zero workers within 2 minutes after the queue drains.

**Constraints**: Endpoint `http://localhost:4566` from the host and `http://host.docker.internal:4566` from pods. Region `us-east-1`. Credentials `test` / `test`. Maximum 5 workers. One worker per 5 visible messages. Visibility timeout 30 seconds. Redrive after 3 receives.

**Scale/Scope**: One API deployment, one worker deployment, one CronJob, two new queues. The order pipeline is out of scope.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. LocalStack es el único AWS**: PASS. Clients use the local gateway only.
- **II. Terraform declara la infraestructura**: PASS. The new queues are Terraform resources. The Nest processes are not Lambda functions, so they do not go under `lambda/`.
- **III. Spec antes del cambio**: PASS. This plan follows `specs/001-keda-jobs/spec.md`.
- **IV. Permiso mínimo**: PASS. The publisher may only send to `demo-jobs`. The worker may only receive, delete, and read attributes on `demo-jobs` and `demo-jobs-dlq`.
- **V. Rastreo**: PASS. The HTTP response returns the queue message id. The worker logs the job id. Three failures land in the dead-letter queue.

Post-design re-check: the contracts and data model do not add a real AWS endpoint, a second source of queue definitions, or access to `demo-orders`. Gate still passes.

## Project Structure

### Documentation (this feature)

```text
specs/001-keda-jobs/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── jobs-api.md
│   └── queue-message.md
└── tasks.md
```

### Source Code (repository root)

```text
jobs/
├── package.json
├── tsconfig.json
├── Dockerfile
├── src/
│   ├── main.ts
│   ├── worker.ts
│   ├── jobs.module.ts
│   ├── jobs.controller.ts
│   ├── jobs.service.ts
│   └── worker-loop.ts
└── test/
    └── jobs.service.test.ts

k8s/
├── kind-config.yaml
├── namespace.yaml
├── api-deployment.yaml
├── worker-deployment.yaml
├── scaledobject.yaml
└── cronjob.yaml

terraform/jobs.tf
```

**Structure Decision**: One Nest project with two entrypoints, because the API and the subscriber share the queue client and the job shape. Kubernetes manifests stay in `k8s/`. Queue resources stay in Terraform.

## Complexity Tracking

No constitution violations.
