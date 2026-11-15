import { SQSClient } from "@aws-sdk/client-sqs"

export function queueUrl(): string {
  const url = process.env.JOBS_QUEUE_URL
  if (!url) {
    throw new Error("JOBS_QUEUE_URL is required")
  }
  return url
}

export function createClient(): SQSClient {
  return new SQSClient({
    region: process.env.AWS_REGION ?? "us-east-1",
    endpoint: process.env.AWS_ENDPOINT_URL ?? "http://localhost:4566",
    credentials: {
      accessKeyId: process.env.AWS_ACCESS_KEY_ID ?? "test",
      secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY ?? "test",
    },
  })
}
