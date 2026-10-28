# syntax=docker/dockerfile:1
#
# Learnora web image: Vite builds the SPA, nginx serves it and proxies /api to
# the API container. One origin, so no CORS and no separate frontend host.
#
#   docker build -t learnora-web --build-arg VITE_API_BASE_URL=/api/v1 ./frontend

# ---- Build stage -----------------------------------------------------------
FROM node:20-alpine AS build

WORKDIR /app

# Dependencies first: this layer only rebuilds when the lockfile changes.
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY . .

# Baked into the bundle at build time. Relative by default so the browser talks
# to nginx, which forwards /api to the API container.
ARG VITE_API_BASE_URL=/api/v1
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build

# ---- Runtime stage ---------------------------------------------------------
FROM nginx:1.27-alpine AS runtime

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --spider http://127.0.0.1/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
