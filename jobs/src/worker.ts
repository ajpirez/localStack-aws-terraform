import { createClient, queueUrl } from "./sqs"
import { pollOnce } from "./worker-loop"

async function main() {
  const client = createClient()
  const queue = queueUrl()
  console.log(JSON.stringify({ worker: "started", queue }))
  for (;;) {
    try {
      await pollOnce(client, queue)
    } catch (error) {
      console.error(JSON.stringify({ worker: "error", detail: String(error) }))
      await new Promise((resolve) => setTimeout(resolve, 1000))
    }
  }
}

main()
