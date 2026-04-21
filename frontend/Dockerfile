# Multi-stage build for frontend
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
# Use npm install if no lock file, otherwise npm ci
RUN if [ -f package-lock.json ]; then npm ci --only=production; else npm install --only=production; fi

FROM node:18-alpine

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder --chown=nodejs:nodejs /app/node_modules ./node_modules

# Copy application code
COPY --chown=nodejs:nodejs . .

# Switch to non-root user
USER nodejs

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000/health', (r) => {r.statusCode === 200 ? process.exit(0) : process.exit(1)})" || exit 1

EXPOSE 3000

CMD ["node", "app.js"]
