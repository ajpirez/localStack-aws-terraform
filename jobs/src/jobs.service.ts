import { SendMessageCommand } from "@aws-sdk/client-sqs"
import { Injectable } from "@nestjs/common"
import { buildJob, type JobMessage } from "./job"
import { createClient, queueUrl } from "./sqs"

@Injectable()
export class JobsService {
  async publish(input: { type?: string; jobId?: string } = {}): Promise<{
    messageId: string
    job: JobMessage
  }> {
    const job = buildJob(input)
    const result = await createClient().send(
      new SendMessageCommand({
        QueueUrl: queueUrl(),
        MessageBody: JSON.stringify(job),
        MessageAttributes: {
          type: { DataType: "String", StringValue: job.type },
          jobId: { DataType: "String", StringValue: job.jobId },
        },
      }),
    )
    if (!result.MessageId) {
      throw new Error("queue did not return a message id")
    }
    return { messageId: result.MessageId, job }
  }
}
