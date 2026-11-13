# Research: Scale job workers with demand

## Decision: NestJS with two entrypoints

- **Decision**: One NestJS application. `src/main.ts` serves HTTP. `src/worker.ts` long-polls the queue.
- **Rationale**: The API and the subscriber share the job shape and the SQS client. Two packages would duplicate that.
- **Alternatives considered**: A second language for the worker. Rejected because the user asked for a Nest API and a subscriber of that work.

## Decision: bun for the Node toolchain

- **Decision**: Create the project and install dependencies with bun. The container runs `bun`.
- **Rationale**: The repo owner prefers bun for installs.
- **Alternatives considered**: npm. Rejected for that preference.

## Decision: kind on Docker Desktop

- **Decision**: A one-node kind cluster. Pods call LocalStack at `http://host.docker.internal:4566`.
- **Rationale**: The user chose kind. LocalStack stays in its current Compose container. Docker Desktop resolves `host.docker.internal` from kind nodes.
- **Alternatives considered**: k3d, and moving LocalStack into the cluster. Rejected. The user chose kind and the emulator is already running on the host.

## Decision: KEDA aws-sqs-queue scaler

- **Decision**: `ScaledObject` with trigger `aws-sqs-queue`, `queueLength: "5"`, `minReplicaCount: 0`, `maxReplicaCount: 5`, `awsEndpoint` set to the LocalStack URL.
- **Rationale**: KEDA's SQS scaler maps visible message count to replica count. Zero minimum satisfies the idle requirement.
- **Alternatives considered**: A custom metrics adapter. Rejected because KEDA already ships this trigger.

## Decision: CronJob calls the API

- **Decision**: A Kubernetes CronJob every minute runs `curl -X POST` against the in-cluster API service.
- **Rationale**: Scheduled work must use the same acceptance path as an operator. Calling SQS from the cron would skip that path.
- **Alternatives considered**: An AWS CLI container that sends directly to SQS. Rejected because it bypasses acceptance.

## Decision: Terraform owns the new queues

- **Decision**: `demo-jobs` and `demo-jobs-dlq` are added in `terraform/jobs.tf`. Visibility timeout 30 seconds. Redrive max receive count 3.
- **Rationale**: Constitution II. The redrive numbers match the existing order queue.
- **Alternatives considered**: Creating the queues from the Nest app at startup. Rejected because Terraform would not know them.
