FROM node:26-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

# Build with placeholder — actual API URL injected at runtime via env
ENV NEXT_PUBLIC_API_URL=http://localhost:8000
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
