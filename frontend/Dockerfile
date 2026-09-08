# Development image. Production is defined in Dockerfile.prod.
FROM node:24-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --no-audit --no-fund
COPY . .
EXPOSE 5173
