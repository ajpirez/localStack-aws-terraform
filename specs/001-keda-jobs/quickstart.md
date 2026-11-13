# Quickstart: Scale job workers with demand

Validates [spec.md](./spec.md) against the running system. Contracts: [jobs-api.md](./contracts/jobs-api.md), [queue-message.md](./contracts/queue-message.md).

## Prerequisites

- Docker Desktop running.
- `kubectl`, `kind`, and `helm` on the PATH.
- LocalStack up: `./scripts/up` from the repo root.
- Queues applied: `cd terraform && terraform apply`.

## Start the cluster

From the repo root:

```bash
kind create cluster --config k8s/kind-config.yaml
helm repo add kedacore https://kedacore.github.io/charts
helm repo update
helm upgrade --install keda kedacore/keda --namespace keda --create-namespace
kubectl -n keda patch deployment keda-operator --type strategic --patch-file k8s/keda-operator-hostalias.yaml
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/worker-deployment.yaml
kubectl apply -f k8s/scaledobject.yaml
kubectl apply -f k8s/cronjob.yaml
kubectl -n jobs rollout status deployment/jobs-api
```

## Checks

```bash
kubectl -n jobs port-forward svc/jobs-api 3000:3000
```

In another terminal:

```bash
curl -s http://127.0.0.1:3000/health
curl -s -X POST http://127.0.0.1:3000/jobs \
  -H 'content-type: application/json' \
  -d '{"type":"manual","jobId":"job-1001"}'
```

Expected: health returns `{"status":"ok"}`. The post returns `201` and a `messageId`.

```bash
cd terraform
../scripts/awslocal sqs get-queue-attributes \
  --queue-url "$(terraform output -raw jobs_queue_url)" \
  --attribute-names ApproximateNumberOfMessages
kubectl -n jobs get pods
```

Expected after the worker runs: the visible count returns to 0 and worker pods scale back toward 0. A second post of six jobs can show more than one worker pod, never more than five.

Leave the CronJob for two minutes, then confirm two messages with `"type":"scheduled"` were accepted by reading the API logs:

```bash
kubectl -n jobs logs deployment/jobs-api --since=3m
```

The order pipeline is unchanged:

```bash
../scripts/awslocal sqs list-queues
../scripts/awslocal sns list-topics
```

`demo-orders` and `demo-events` are still present. `demo-jobs` is additional.
