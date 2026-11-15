# Research: Check the lab on every change

## Decision: GitHub-hosted Ubuntu runs the check

**Rationale**: A published change must be checked away from the developer Mac. GitHub Actions starts a clean machine per run and discards it afterward. The token is the repository secret `LOCALSTACK_AUTH_TOKEN`.

**Alternatives considered**: Running the check on the Mac by hand keeps the current lab and does not satisfy a check that starts by itself. A self-hosted runner would still be this Mac.

## Decision: `./scripts/up` chooses the socket

**Rationale**: The constitution says the lab starts with `./scripts/up` and that this Mac mounts `~/.docker/run/docker.sock`. The runner has `/var/run/docker.sock` and does not have the Mac path. The script keeps the Mac path when that socket exists and otherwise uses the Linux path. One compose file stays.

**Alternatives considered**: A second compose file for CI would start LocalStack without `scripts/up` and would duplicate the service.

## Decision: Pods reach LocalStack by its address on the kind network

**Rationale**: The manifests point host names at `192.168.65.254`, which is Docker Desktop on this Mac. On the runner that address refuses connections. After kind exists, the workflow connects the LocalStack container to the `kind` network and replaces `192.168.65.254` with that container's IP before apply. From the runner host, Terraform and `curl` still use `http://127.0.0.1:4566`.

**Alternatives considered**: Publishing port 4566 on every interface and using the bridge gateway is fragile on the kind network. Hard-coding a second IP in the manifests would break the Mac.

## Decision: LocalStack ignores the declared CPU and uses the machine image

**Rationale**: The check failed with `exec format error` on `/var/runtime/bootstrap` while the functions were arm64 and the runner is x86_64. Setting `TF_VAR_lambda_architecture=x86_64` still lets LocalStack start the image named by the declared CPU (`--platform linux/arm64` or `linux/amd64`). FR-011 says the declared CPU must not choose the image. `LAMBDA_IGNORE_ARCHITECTURE=1` on the LocalStack service makes that choice empty, and Docker pulls the image of the machine running the container. The value has to be in `docker-compose.yml`, because an environment variable on the workflow step does not enter the container. On this Mac the machine image is arm64, so the running functions stay on the CPU they already use. The Terraform default stays `arm64`. The workflow does not set `TF_VAR_lambda_architecture`.

**Alternatives considered**: Keeping `TF_VAR_lambda_architecture=x86_64` makes the declaration choose the image, which the clarification rejected, and the same `exec format error` can remain. Switching the Terraform default to x86_64 would change the declaration used on this Mac. Installing QEMU so the runner can execute an arm64 image keeps the wrong image and slows the check.

## Decision: One job proves the worker; the schedule runs once

**Rationale**: The worker deletes a message in under a second, and KEDA counts every 10 seconds. Twenty-five messages with the worker running do not stay visible long enough to show five pods. The check submits `job-ci-1`, waits until a worker logs it, and reads `maxReplicaCount` equal to 5. It then creates one Job from `jobs-schedule` so the schedule path runs without waiting for the next minute.

**Alternatives considered**: Pausing the worker with `sleep 300` shows five pods and leaves the cluster in a state the check would have to undo. Waiting for the clock makes the check fail when the minute boundary is unlucky.
