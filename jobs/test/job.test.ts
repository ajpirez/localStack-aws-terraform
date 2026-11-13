import { describe, expect, test } from "bun:test"
import { buildJob, shouldFail } from "../src/job"

describe("buildJob", () => {
  test("defaults type to manual and fills jobId", () => {
    const job = buildJob({}, new Date("2026-11-13T20:00:00.000Z"))
    expect(job.type).toBe("manual")
    expect(job.jobId.length).toBeGreaterThan(0)
    expect(job.requestedAt).toBe("2026-11-13T20:00:00.000Z")
  })

  test("keeps a caller-supplied type and jobId", () => {
    const job = buildJob({ type: "scheduled", jobId: "job-1001" }, new Date("2026-11-13T20:00:00.000Z"))
    expect(job).toEqual({
      type: "scheduled",
      jobId: "job-1001",
      requestedAt: "2026-11-13T20:00:00.000Z",
    })
  })
})

describe("shouldFail", () => {
  test("fails only the fail type", () => {
    expect(shouldFail({ type: "fail", jobId: "a", requestedAt: "t" })).toBe(true)
    expect(shouldFail({ type: "manual", jobId: "a", requestedAt: "t" })).toBe(false)
  })
})
