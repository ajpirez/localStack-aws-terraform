import {
  Body,
  Controller,
  Get,
  HttpCode,
  Post,
  ServiceUnavailableException,
} from "@nestjs/common"
import { JobsService } from "./jobs.service"

@Controller()
export class JobsController {
  constructor(private readonly jobs: JobsService) {}

  @Get("health")
  health() {
    return { status: "ok" }
  }

  @Post("jobs")
  @HttpCode(201)
  async create(@Body() body: { type?: string; jobId?: string } = {}) {
    try {
      const accepted = await this.jobs.publish(body)
      console.log(
        JSON.stringify({
          accepted: true,
          messageId: accepted.messageId,
          type: accepted.job.type,
          jobId: accepted.job.jobId,
        }),
      )
      return accepted
    } catch (error) {
      console.error(JSON.stringify({ error: "queue unavailable", detail: String(error) }))
      throw new ServiceUnavailableException({ error: "queue unavailable" })
    }
  }
}
