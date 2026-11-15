# Contract: Queue message

Queue: `demo-jobs`

Body, JSON:

```json
{
  "type": "manual",
  "jobId": "job-1001",
  "requestedAt": "2026-11-13T20:00:00.000Z"
}
```

Message attributes:

- `type`: String
- `jobId`: String

A worker logs `jobId` and `messageId`, then deletes the message. If the worker throws, it does not delete the message. After three receives, SQS moves the message to `demo-jobs-dlq` with the same body.
