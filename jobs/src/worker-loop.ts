import {
  DeleteMessageCommand,
  ReceiveMessageCommand,
  type Message,
  type SQSClient,
} from "@aws-sdk/client-sqs"
import { shouldFail, type JobMessage } from "./job"

export function parseJob(body: string): JobMessage {
  const parsed = JSON.parse(body) as Partial<JobMessage>
  if (!parsed.type || !parsed.jobId || !parsed.requestedAt) {
    throw new Error("job message is missing type, jobId, or requestedAt")
  }
  return {
    type: parsed.type,
    jobId: parsed.jobId,
    requestedAt: parsed.requestedAt,
  }
}

export async function handleMessage(client: SQSClient, queue: string, message: Message) {
  if (!message.Body || !message.ReceiptHandle) {
    return
  }
  const job = parseJob(message.Body)
  console.log(JSON.stringify({ jobId: job.jobId, messageId: message.MessageId, type: job.type }))
  if (shouldFail(job)) {
    throw new Error(`job ${job.jobId} failed on purpose`)
  }
  await client.send(
    new DeleteMessageCommand({
      QueueUrl: queue,
      ReceiptHandle: message.ReceiptHandle,
    }),
  )
}

export async function pollOnce(client: SQSClient, queue: string) {
  const result = await client.send(
    new ReceiveMessageCommand({
      QueueUrl: queue,
      MaxNumberOfMessages: 1,
      WaitTimeSeconds: 20,
      MessageAttributeNames: ["All"],
    }),
  )
  for (const message of result.Messages ?? []) {
    await handleMessage(client, queue, message)
  }
}
