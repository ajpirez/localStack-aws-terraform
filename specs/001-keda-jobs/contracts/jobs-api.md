# Contract: Jobs API

Base URL inside the cluster: `http://jobs-api.jobs.svc.cluster.local`

From the host, after a port-forward to local port 3000: `http://127.0.0.1:3000`

## GET /health

Response `200`:

```json
{ "status": "ok" }
```

## POST /jobs

Request body, all fields optional:

```json
{
  "type": "manual",
  "jobId": "job-1001"
}
```

Response `201`:

```json
{
  "messageId": "generated-by-the-queue",
  "job": {
    "type": "manual",
    "jobId": "job-1001",
    "requestedAt": "2026-11-13T20:00:00.000Z"
  }
}
```

Response `503` when the local queue cannot accept the message. The body is:

```json
{ "error": "queue unavailable" }
```

The scheduled caller sends `{ "type": "scheduled" }` and omits `jobId`.
