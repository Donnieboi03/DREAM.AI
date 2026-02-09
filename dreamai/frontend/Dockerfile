# Build stage
FROM node:18-alpine as builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Production stage
FROM node:18-alpine

WORKDIR /app

# Install serve to run the production build
RUN npm install -g serve

COPY --from=builder /app/dist ./dist

EXPOSE 5173

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget -q -O- http://localhost:5173 || exit 1

CMD ["serve", "-s", "dist", "-l", "5173"]
