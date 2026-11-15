export type JobMessage = {
  type: string
  jobId: string
  requestedAt: string
}

export function buildJob(
  input: { type?: string; jobId?: string } = {},
  now = new Date(),
): JobMessage {
  const type = (input.type ?? "").trim() || "manual"
  const jobId = (input.jobId ?? "").trim() || crypto.randomUUID()
  return { type, jobId, requestedAt: now.toISOString() }
}

export function shouldFail(job: JobMessage): boolean {
  return job.type === "fail"
}
