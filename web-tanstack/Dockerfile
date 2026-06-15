# GraphMind Frontend - 多阶段构建
# Stage 1: 构建静态文件
FROM node:22-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

ENV VITE_API_BASE_URL=
RUN npm run build

# Stage 2: Nginx 托管 + 反向代理
FROM nginx:1.27-alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
