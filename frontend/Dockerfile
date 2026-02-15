# ============================================================================
# LeadGen Intelligence Pipeline - Frontend Dockerfile
# Runs Next.js on Railway
#
# API calls go through a server-side proxy route handler.
# Set BACKEND_URL env var at runtime to the backend service URL.
# On Railway internal networking: BACKEND_URL=http://google-maps-scraper.railway.internal:8000
# ============================================================================

# Dependencies stage
FROM node:22-alpine AS deps
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --production=false

# Build stage
FROM node:22-alpine AS builder
WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build the Next.js application (standalone output)
# No build-time env vars needed — BACKEND_URL is read at runtime
RUN npm run build

# Production stage
FROM node:22-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy built assets from builder
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# BACKEND_URL is read at runtime by the API proxy route handler.
# Set this on Railway to: http://google-maps-scraper.railway.internal:8000
ENV BACKEND_URL=""

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

CMD ["node", "server.js"]
