# ============================================================
# Stage 1: Development
# ============================================================
FROM node:20-alpine AS development

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies with retry logic and proper fallback
RUN if [ -f package-lock.json ]; then \
        npm ci --prefer-offline --no-audit --legacy-peer-deps || \
        npm install --prefer-offline --no-audit --legacy-peer-deps; \
    else \
        npm install --prefer-offline --no-audit --legacy-peer-deps; \
    fi

# Copy source (will be overridden by volume mount in dev)
COPY . .

# Expose Vite dev server port
EXPOSE 3000

# Start development server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]

# ============================================================
# Stage 2: Builder
# ============================================================
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies with fallback
RUN if [ -f package-lock.json ]; then \
        npm ci --prefer-offline --no-audit --production=false --legacy-peer-deps || \
        npm install --prefer-offline --no-audit --legacy-peer-deps; \
    else \
        npm install --prefer-offline --no-audit --legacy-peer-deps; \
    fi

# Copy source code
COPY . .

# Build production bundle
RUN npm run build

# ============================================================
# Stage 3: Production
# ============================================================
FROM nginx:1.25-alpine AS production

# Install curl for healthchecks
RUN apk add --no-cache curl

# Remove default nginx config
RUN rm -rf /etc/nginx/conf.d/*

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Create nginx cache directory
RUN mkdir -p /var/cache/nginx && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /usr/share/nginx/html

# Expose port
EXPOSE 3000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000 || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
