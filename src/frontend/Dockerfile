# Build stage - use Debian (node:18-slim) to avoid Alpine musl + Rollup optional deps bug
FROM node:18-slim as builder

WORKDIR /app
COPY package.json ./
# Workaround npm optional deps bug (https://github.com/npm/cli/issues/4828):
# Use npm install (no lockfile) so Rollup gets correct linux binary in container
RUN npm install

COPY . .
RUN npm run build

# Production stage
FROM node:18-slim

WORKDIR /app

# Install serve to run the production build
RUN npm install -g serve

COPY --from=builder /app/dist ./dist

EXPOSE 5173

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget -q -O- http://localhost:5173 || exit 1

CMD ["serve", "-s", "dist", "-l", "5173"]
