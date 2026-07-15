FROM node:24-alpine AS build
RUN corepack enable
WORKDIR /app
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml* ./
COPY apps/web/package.json apps/web/package.json
RUN pnpm install --frozen-lockfile
COPY apps/web apps/web
RUN pnpm --filter web build
FROM node:24-alpine
RUN addgroup -S scopeguard && adduser -S -G scopeguard -u 10001 scopeguard
WORKDIR /app
COPY --from=build --chown=scopeguard:scopeguard /app/apps/web/.next/standalone ./
COPY --from=build --chown=scopeguard:scopeguard /app/apps/web/.next/static ./apps/web/.next/static
USER scopeguard
EXPOSE 3000
CMD ["node", "apps/web/server.js"]

