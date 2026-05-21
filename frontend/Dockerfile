# Step 1: Build the React Application
FROM node:20-slim AS build

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

RUN npm run build

# Step 2: Serve using Nginx
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration if needed, otherwise use default
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
