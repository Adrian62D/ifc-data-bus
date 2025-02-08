# Use the official Nginx image as the base image
FROM nginx:alpine

# Remove the default Nginx static assets
RUN rm -rf /usr/share/nginx/html/*

COPY index.html /usr/share/nginx/html

# Expose port 80 to be accessible outside the container
EXPOSE 80

# Start Nginx in the foreground
CMD ["nginx", "-g", "daemon off;"]
