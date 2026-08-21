import { z } from "zod";

/** Matches the provider-neutral service identity accepted by the v1 API. */
export const SERVICE_NAME_PATTERN = /^[a-z][a-z0-9-]*$/;

/** Runtime validator for the stable v1 process-liveness response. */
export const healthLiveResponseSchema = z
  .object({
    status: z.literal("ok"),
    service: z.string().min(3).max(63).regex(SERVICE_NAME_PATTERN),
    api_version: z.literal("v1"),
  })
  .strict();

export type HealthLiveResponse = z.infer<typeof healthLiveResponseSchema>;
