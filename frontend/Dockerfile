# Étape de build
FROM node:21.4.0 AS builder

WORKDIR /usr/src/app

COPY package.json yarn.lock ./

RUN yarn install --frozen-lockfile

COPY . .

RUN yarn build

# Étape de production
FROM node:21.4.0-alpine

WORKDIR /usr/src/app

COPY --from=builder /usr/src/app/package.json /usr/src/app/yarn.lock ./
COPY --from=builder /usr/src/app/.next ./.next
COPY --from=builder /usr/src/app/public ./public

RUN yarn install --production --frozen-lockfile

EXPOSE 3000

CMD ["yarn", "start"]
