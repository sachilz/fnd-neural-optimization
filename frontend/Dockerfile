# Stage 1: Build the React application
FROM node:20-alpine AS build

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
# The build will read VITE_API_URL if injected via --build-arg, but for simplicity 
# we allow it to be injected or default to http://localhost:8000 which works for most Docker use-cases.
RUN npm run build

# Stage 2: Serve the application using Nginx
FROM nginx:alpine

# Copy custom nginx config if necessary, or just use default and overwrite html
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom nginx config to enable reverse proxying to backend
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 5173

CMD ["nginx", "-g", "daemon off;"]
