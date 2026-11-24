FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev

FROM nginx:1.27-alpine
COPY --from=deps /app/node_modules /usr/share/nginx/html/node_modules
COPY index.html /usr/share/nginx/html/
COPY app /usr/share/nginx/html/app
