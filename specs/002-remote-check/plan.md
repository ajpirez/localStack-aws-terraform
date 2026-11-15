# Implementation Plan: Check the lab on every change

**Branch**: `002-remote-check` | **Date**: 2026-11-15 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-remote-check/spec.md`

## Summary

A GitHub Actions workflow reruns the local lab on a clean Ubuntu runner whenever a change is published. It starts LocalStack with `./scripts/up`, applies Terraform from `terraform/`, builds `jobs-api:local`, and loads it into the existing kind cluster. KEDA and the CronJob stay as declared in `k8s/`. The check accepts `job-ci-1`, waits until a worker logs that identifier, and runs the CronJob template once. The Mac socket remains the default. The runner uses `/var/run/docker.sock` only when the Mac socket is absent. The token comes from the Actions secret `LOCALSTACK_AUTH_TOKEN` and is never written into a tracked file. LocalStack ignores the CPU declared on the functions and starts the runtime image of the machine that is running the check. On this Mac that image stays arm64.

## Technical Context

**Language/Version**: GitHub Actions on `ubuntu-latest`. Existing TypeScript Nest app and Terraform `>= 1.5.0` stay as they are.

**Primary Dependencies**: Docker Compose, Terraform, kind v0.33.0, kubectl v1.33.4, Helm v3.17.3, bun 1.4.4 for the unit test

**Storage**: No new store. The runner discards LocalStack when the job ends. `PERSISTENCE` stays 0.

**Testing**: `bun test` in `jobs/` on every run, then one stack job that calls the API, reads the worker log, and completes one CronJob pod.

**Target Platform**: GitHub-hosted Ubuntu for the check. Docker Desktop on this Mac for the lab.

**Project Type**: CI workflow plus a small start-script change so both machines can run `./scripts/up`

**Performance Goals**: The stack job reports pass or fail within 40 minutes.

**Constraints**: LocalStack only, `http://localhost:4566`, region `us-east-1`, credentials `test` / `test`. Pods cannot use the Mac address `192.168.65.254`. The workflow rewrites that address to the LocalStack container IP on the kind network before `kubectl apply`. Maximum workers stays 5. The check does not pause the worker to force five replicas. `docker-compose.yml` sets `LAMBDA_IGNORE_ARCHITECTURE=1` on the LocalStack service, so the declared CPU does not choose the runtime image. Docker uses the image of the machine running `./scripts/up`. On this Mac that image is arm64. The Terraform default stays `arm64` and the workflow does not pass `TF_VAR_lambda_architecture`.

**Scale/Scope**: One workflow file, one socket choice in `scripts/up`, and one LocalStack environment entry in `docker-compose.yml`. No new queues and no change to the Nest handlers.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. LocalStack es el único AWS**: PASS. The runner talks to LocalStack on `localhost:4566`. `./scripts/up` remains the start command. The Mac socket stays the default; `/var/run/docker.sock` is used only when that socket is not on the machine.
- **II. Terraform declara la infraestructura**: PASS. The check runs `terraform apply` from `terraform/`. It does not create queues with a side script.
- **III. Spec antes del cambio**: PASS. This plan follows `specs/002-remote-check/spec.md`.
- **IV. Permiso mínimo**: PASS. No new roles. The existing publisher and worker policies stay as they are.
- **V. Rastreo**: PASS. The check requires the worker log to contain `job-ci-1`, the same identifier returned by the acceptance call.

Post-design re-check: the contract is the check's observable results, not a new public API. The token is an Actions secret. The runtime image follows the machine through one LocalStack setting in the existing compose file; Terraform still owns the functions. Gate still passes.

## Project Structure

### Documentation (this feature)

```text
specs/002-remote-check/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── check-run.md
└── tasks.md
```

### Source Code (repository root)

```text
.github/workflows/ci.yml
scripts/up
docker-compose.yml
```

**Structure Decision**: The workflow is the check. `scripts/up` learns which Docker socket exists so the Mac and the runner share one start command. `docker-compose.yml` tells LocalStack to ignore the declared CPU. `k8s/` and `jobs/` stay as implemented for `001-keda-jobs`.
