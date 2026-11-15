# Data Model: Check the lab on every change

No new stored records. The check observes entities that already exist.

## Check run

- **Identity**: one workflow run for one published change
- **Outcome**: pass or fail
- **Lifetime**: the runner machine is discarded at the end
- **Secret**: `LOCALSTACK_AUTH_TOKEN` is present in the run environment and absent from tracked files

## Accepted job

- **Identifier**: `job-ci-1`
- **Type**: `manual`
- **Evidence**: HTTP acceptance body contains `job-ci-1`. A worker log line contains the same identifier.

## Scheduled submission

- **Source**: one run of the existing schedule path
- **Evidence**: that run completes successfully
- **Relationship**: it uses the same acceptance path as the accepted job

## Worker bound

- **Resting count**: zero workers when nothing is waiting, already the deployment default
- **Upper bound**: five, read from the installed worker rule during the check
