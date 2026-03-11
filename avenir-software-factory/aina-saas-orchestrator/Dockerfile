FROM node:20-alpine

WORKDIR /app

# Installation de OpenSSL, requis par Prisma sur Alpine
RUN apk add --no-cache openssl

COPY package*.json ./
RUN npm install

# Copier le schéma Prisma et générer le client
COPY prisma ./prisma
RUN npx prisma generate

# Copier le reste du code
COPY . .

CMD ["sh", "-c", "npx prisma db push && npx ts-node src/server.ts"]
