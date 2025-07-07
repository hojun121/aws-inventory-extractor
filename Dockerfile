# Build Python module to excuable on linux
FROM ubuntu:22.04 AS builder
WORKDIR /build
# Copy source code and install dependencies
COPY . .
RUN apt-get update -y \
 && apt-get install -y build-essential libpq-dev python3 python3-pip -y \
 && pip install -r python/requirements.txt \
 && pip install pyinstaller \
 && pyinstaller --onefile \
        --add-data "./python/modules:modules" \
        --add-data "./python/templates:templates" \
        --name inventory_binary \
        python/app.py

# Stage 2: Create a lightweight image for the executable
FROM debian:12-slim
WORKDIR /app
ENV IS_CONTAINER=true
# Copy the compiled binary and required scripts
COPY --from=builder /build/dist/inventory_binary .
COPY --from=builder /build/run_script.sh .
# Install AWS CLI and additional tools
RUN apt-get update -y \
 && apt-get install -y curl unzip lolcat cowsay less jq \
 && curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
 && unzip awscliv2.zip \
 && ./aws/install \
 && rm -rf awscliv2.zip /var/lib/apt/lists/* /tmp/* /usr/share/doc/* /usr/share/man/* /usr/share/info/* \
 && apt-get clean \
 && chmod 777 inventory_binary \
 && chmod 777 run_script.sh
# Setup Entrypoint
ENTRYPOINT ["/app/run_script.sh"]