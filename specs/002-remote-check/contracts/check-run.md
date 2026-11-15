# Contract: Check run

A published change produces one check run. The run passes only when every line below is true.

## Start

- LocalStack becomes ready at `http://127.0.0.1:4566` after `./scripts/up`.
- The access token is not written to a tracked file.
- If the token is missing, the run fails at start.

## Infrastructure

- `terraform apply` from `terraform/` finishes without error, including the invocation of the publisher function.
- The function image that starts matches the machine running the check. The declared CPU does not choose that image. On this Mac the image that starts stays arm64.
- The order pipeline and `demo-jobs` both exist afterward.

## Acceptance and worker

- `GET /health` returns a body with `"status":"ok"`.
- `POST /jobs` with `{"type":"manual","jobId":"job-ci-1"}` returns a body that contains `"jobId":"job-ci-1"`.
- A worker log line contains `"jobId":"job-ci-1"`.

## Schedule and bound

- The installed worker rule reports a maximum of 5.
- One run of the schedule path completes successfully.

## Developer machine

- On this Mac, `./scripts/up` still mounts `~/.docker/run/docker.sock`.
- On this Mac, a `terraform apply` without an extra variable still records the functions as arm64, and the image that starts is still arm64.
