FROM nginx:alpine

# Copy static frontend SPA assets to Nginx default html directory
COPY frontend/index.html /usr/share/nginx/html/index.html
COPY frontend/app.js /usr/share/nginx/html/app.js

EXPOSE 80
