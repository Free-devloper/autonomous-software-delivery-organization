import { z } from "zod";

export const deploymentEnvironmentSchema = z.enum([
  "local",
  "ci",
  "development",
  "staging",
  "production",
  "dr",
]);

const publicWebConfigSchema = z
  .object({
    NEXT_PUBLIC_ASDO_API_BASE_URL: z
      .url({ protocol: /^https?$/u, normalize: true })
      .transform((value) => new URL(value))
      .refine(
        (url) =>
          (url.protocol === "http:" || url.protocol === "https:") && !url.username && !url.password,
        { message: "API base URL must use HTTP or HTTPS and must not contain credentials" },
      ),
    NEXT_PUBLIC_ASDO_ENVIRONMENT: deploymentEnvironmentSchema,
  })
  .strict();

export type DeploymentEnvironment = z.infer<typeof deploymentEnvironmentSchema>;
export type PublicWebConfig = Readonly<{
  apiBaseUrl: string;
  environment: DeploymentEnvironment;
}>;

export function parsePublicWebConfig(input: unknown): PublicWebConfig {
  const parsed = publicWebConfigSchema.parse(input);
  return Object.freeze({
    apiBaseUrl: parsed.NEXT_PUBLIC_ASDO_API_BASE_URL.href.replace(/\/$/u, ""),
    environment: parsed.NEXT_PUBLIC_ASDO_ENVIRONMENT,
  });
}
