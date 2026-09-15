FROM node:20-alpine AS base

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy source code
COPY . .

ENV PORT=3000
ENV NODE_ENV=production
ENV API_BASE_URL=http://backend:8000

# Build Next.js application
RUN npm run build

# Expose port
EXPOSE 3000

CMD ["npm", "start"]
