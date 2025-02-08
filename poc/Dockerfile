# Use Alpine as the base image for a minimal footprint
FROM emqx/nanomq:0.18.2-full

# Set environment variables
ENV NANOMQ_VERSION=0.18.2

# Install necessary dependencies
# RUN apk add --no-cache git build-base cmake ninja libuv-dev openssl-dev \
#     && git clone --depth 1 --branch v$NANOMQ_VERSION https://github.com/nanomq/nanomq.git \
#     && cd nanomq \
#     && cmake -Bbuild -G Ninja -DCMAKE_BUILD_TYPE=Release \
#     && cmake --build build \
#     && cmake --install build \
#     && cd .. \
#     && rm -rf nanomq \
#     && apk del git build-base cmake ninja

# Set working directory
WORKDIR /etc/nanomq

# Expose default MQTT ports
EXPOSE 1883 8883 8083 8084

# Command to start NanoMQ
ENTRYPOINT ["nanomq"]

# Default arguments (can be overridden)
CMD ["start"]
