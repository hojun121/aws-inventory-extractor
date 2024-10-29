# Build Python module to excuable on linux
FROM ubuntu:22.04 AS builder
RUN apt-get update -y \
 && apt-get install -y sudo build-essential libpq-dev python3 python3-pip -y \
 && pip install pandas openpyxl xlsxwriter SQLAlchemy psycopg2 tqdm pyinstaller \
 && export PATH=$PATH:~/.local/bin
COPY . .
RUN pyinstaller --onefile --add-data "python/pre_processor/modules:modules" --name pre_processor_binary python/pre_processor/__init__.py \
 && pyinstaller --onefile --distpath ./dist_raw_data --name raw_data_binary python/raw_data/__init__.py

# Lightweight base-image
FROM debian:12-slim
# Install awscli & steampipe
USER root
RUN apt-get update -y \
 && apt-get install -y lolcat cowsay sudo curl less unzip wget jq \
 && curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
 && unzip awscliv2.zip \
 && ./aws/install \
 && rm -rf awscliv2.zip aws/ \
 && curl -fsSL https://github.com/turbot/steampipe/releases/latest/download/steampipe_linux_amd64.deb -o steampipe.deb \
 && apt-get install -y ./steampipe.deb \
 && rm steampipe.deb \
 && useradd -m steampipe  \
 && echo "steampipe ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
# Install steampipe plugin & Copy excuable binary from builder
USER steampipe
SHELL ["/bin/bash", "-c"]
WORKDIR /app
COPY --from=builder dist/pre_processor_binary /app/pre_processor_binary
COPY --from=builder dist_raw_data/raw_data_binary /app/raw_data_binary
COPY --from=builder extract_inventory.sh /app/extract_inventory.sh
RUN steampipe plugin install steampipe aws \
 && sudo mkdir -p output/pre_processed \
 && sudo chmod 777 output/pre_processed \
 && sudo mkdir -p output/raw_data \
 && sudo chmod 777 output/raw_data \
 && sudo chmod 777 pre_processor_binary \
 && sudo chmod 777 raw_data_binary \
 && sudo chmod 777 extract_inventory.sh
ENTRYPOINT ["/app/extract_inventory.sh"]
