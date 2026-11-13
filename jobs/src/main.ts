import "reflect-metadata"
import { NestFactory } from "@nestjs/core"
import { JobsModule } from "./jobs.module"

async function main() {
  const app = await NestFactory.create(JobsModule)
  const port = Number(process.env.PORT ?? 3000)
  await app.listen(port)
}

main()
