FROM node:20-slim

WORKDIR /app
COPY package.json ./
COPY src ./src

ENV NODE_ENV=production
EXPOSE 8080

CMD ["npm", "start"]
