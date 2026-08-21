FROM docker.io/library/node:24.18.0-bookworm-slim@sha256:6f7b03f7c2c8e2e784dcf9295400527b9b1270fd37b7e9a7285cf83b6951452d AS build

WORKDIR /workspace
ENV NEXT_TELEMETRY_DISABLED=1

RUN corepack enable

COPY .npmrc package.json pnpm-lock.yaml pnpm-workspace.yaml tsconfig.base.json ./
COPY apps/web/package.json apps/web/package.json
COPY packages/contracts/package.json packages/contracts/package.json
COPY packages/config/package.json packages/config/package.json
COPY packages/ui/package.json packages/ui/package.json
RUN corepack pnpm install --frozen-lockfile

COPY apps/web apps/web
COPY packages packages
RUN corepack pnpm --filter @asdo/web build

FROM docker.io/library/node:24.18.0-bookworm-slim@sha256:6f7b03f7c2c8e2e784dcf9295400527b9b1270fd37b7e9a7285cf83b6951452d AS runtime

ENV HOSTNAME=0.0.0.0
ENV NODE_ENV=production
ENV PORT=3000
WORKDIR /workspace

RUN groupadd --system --gid 10001 asdo \
  && useradd --system --uid 10001 --gid asdo --home-dir /nonexistent --shell /usr/sbin/nologin asdo

COPY --from=build /workspace/apps/web/.next/standalone ./
COPY --from=build /workspace/apps/web/.next/static apps/web/.next/static
COPY --from=build /workspace/node_modules node_modules
COPY --from=build /workspace/apps/web/node_modules apps/web/node_modules

USER 10001:10001
EXPOSE 3000
CMD ["node", "apps/web/server.js"]
