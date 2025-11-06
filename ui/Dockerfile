# Build stage
FROM node:20-alpine AS build
WORKDIR /app

COPY package.json ./
# если у тебя есть package-lock.json — раскомментируй следующую строку и замени install на ci
# COPY package-lock.json ./

# без lock-файла:
RUN npm install --no-audit --no-fund
# с lock-файлом:
# RUN npm ci --no-audit --no-fund

COPY . .
RUN npm run build

# Serve stage
FROM nginx:1.27-alpine
# Удаляем дефолтный конфиг, чтобы точно не конфликтовал
RUN rm -f /etc/nginx/conf.d/default.conf
# Кладём наш минимальный конфиг как default.conf
COPY nginx.conf /etc/nginx/conf.d/default.conf
# Копируем сборку
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
