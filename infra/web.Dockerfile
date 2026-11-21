FROM node:24-bookworm-slim AS build
WORKDIR /web
COPY apps/web/package*.json ./
RUN npm ci
COPY apps/web/ .
ENV API_INTERNAL_URL=http://api:8000
RUN npm run build
FROM node:24-bookworm-slim
WORKDIR /web
COPY --from=build /web/.next/standalone ./
COPY --from=build /web/.next/static ./.next/static
ENV HOSTNAME=0.0.0.0
USER node
CMD ["node","server.js"]
