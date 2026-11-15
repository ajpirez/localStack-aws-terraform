# Data model: Scale job workers with demand

## Job

| Field | Required | Rule |
|---|---|---|
| type | yes | Non-empty string. Scheduled jobs use `scheduled`. Operator jobs use the value sent by the caller, default `manual`. |
| jobId | yes | Non-empty string. The API generates one when the caller omits it. |
| requestedAt | yes | ISO-8601 timestamp set by the API at acceptance. |

## States

```text
accepted → waiting → in progress → completed
                              └→ waiting (failure, receive count < 3)
                              └→ failed (receive count = 3, moved to the holding area)
```

- **accepted**: the HTTP caller received a message id.
- **waiting**: the message is visible on `demo-jobs`.
- **in progress**: a worker received it and the visibility timeout is running.
- **completed**: the worker deleted it after success.
- **failed**: SQS moved it to `demo-jobs-dlq` after 3 receives.

## Work queue

`demo-jobs`. Holds waiting jobs. Not connected to `demo-events` or `demo-orders`.

## Failed-job holding area

`demo-jobs-dlq`. Receives a job only through the redrive policy of `demo-jobs`.

## Worker

A replica of the subscriber process. Count is 0 when `demo-jobs` has no visible messages. Count increases by one for each group of 5 visible messages, and never exceeds 5.
