# Quickstart: Check the lab on every change

Validates [spec.md](./spec.md). Contract: [check-run.md](./contracts/check-run.md).

## Secret

In the GitHub repository, add an Actions secret named `LOCALSTACK_AUTH_TOKEN`. Use the same value as `.env` on this Mac. Do not commit that value.

## Run

Publish the branch, or open Actions and run the workflow named `ci` by hand.

The unit job runs `bun test` in `jobs/`. The stack job then:

1. Runs `./scripts/up`.
2. Runs `terraform apply` from `terraform/`.
3. Builds `jobs-api:local`, creates the kind cluster, and installs KEDA.
4. Accepts `job-ci-1` and waits for that identifier in a worker log.
5. Runs the schedule path once and expects that run to complete.

A green run is a pass. A red run is a fail. The log of the stack job is the record.

## Mac

`./scripts/up` on this Mac is unchanged in outcome: it still uses `~/.docker/run/docker.sock` when that socket exists.
