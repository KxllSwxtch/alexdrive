# ── Dependencies ─────────────────────────────────────────
FROM node:22-alpine AS deps

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts

# ── Builder ──────────────────────────────────────────────
FROM node:22-alpine AS builder

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Baked into client JS at build time — must be the public URL
ARG NEXT_PUBLIC_BACKEND_URL
ENV NEXT_PUBLIC_BACKEND_URL=$NEXT_PUBLIC_BACKEND_URL

RUN npm run build

# ── Runner ───────────────────────────────────────────────
FROM node:22-alpine

WORKDIR /app

ENV NODE_ENV=production

# Non-root user
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Copy standalone output
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

# Ensure Next.js can write to the cache directory
RUN mkdir -p .next/cache && chown -R appuser:appgroup .next

USER appuser

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://localhost:3000/ || exit 1

# BACKEND_URL is set at runtime for SSR (points to backend via Docker DNS)
CMD ["node", "server.js"]
