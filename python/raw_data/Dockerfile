FROM ubuntu:22.04 AS builder
# Install necessary dependencies
WORKDIR /app
COPY . .
RUN apt-get update -y \
 && apt-get install -y sudo build-essential libpq-dev python3 python3-pip sudo curl less unzip wget apt-utils vim jq \
 && pip install pandas openpyxl xlsxwriter SQLAlchemy psycopg2 tqdm \
 && sudo ln -s /usr/bin/python3 /usr/bin/python \
 && export PATH=$PATH:~/.local/bin \
 && curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
 && unzip awscliv2.zip \
 && ./aws/install \
 && rm -rf awscliv2.zip aws/ \
 && curl -fsSL https://github.com/turbot/steampipe/releases/latest/download/steampipe_linux_amd64.deb -o steampipe.deb \
 && apt-get install -y ./steampipe.deb \
 && rm steampipe.deb \
 && useradd -m steampipe  \
 && echo "steampipe ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Switch to steampipe user and set up environment
USER steampipe
SHELL ["/bin/bash", "-c"]
# Inject Support Command to ~/.bashrc 
RUN echo 'init_sso() {' >> ~/.bashrc \
 && echo '    echo "SetUp AWS SSO & Steampipe Config"' >> ~/.bashrc \
 && echo '    /app/configure_aws_steampipe.sh' >> ~/.bashrc \
 && echo '    echo "\nCheck ~/.aws/config , ~/.steampipe/config/aws.spc"' >> ~/.bashrc \
 && echo '}' >> ~/.bashrc \
 && echo 'init_password() {' >> ~/.bashrc \
 && echo '    export password=$(steampipe service start --show-password | grep "Password:" | awk "{print \$2}")' >> ~/.bashrc \
 && echo '    echo "password initialize: $password"' >> ~/.bashrc \
 && echo '}' >> ~/.bashrc \
 && echo 'cmd() {' >> ~/.bashrc \
 && echo '    source ~/.bashrc' >> ~/.bashrc \
 && echo '}' >> ~/.bashrc \
 && echo -e '\necho -e "\n\033[1;35m[Pre-Requirement] You should run init_sso first to ensure AWS login & Steampipe init\033[0m"' >> ~/.bashrc \
 && echo -e '\necho -e "\n\033[1;34m[Description : Command] Help Command : \033[0mcmd"' >> ~/.bashrc \
 && echo -e '\necho -e "\n\033[1;34m[Description : Command] AWS IAM Login : \033[0maws configure"' >> ~/.bashrc \
 && echo -e '\necho -e "\n\033[1;34m[Description : Command] AWS SSO Initialize : \033[0minit_sso"' >> ~/.bashrc \
 && echo -e '\necho -e "\n\033[1;34m[Description : Command] Initialize Steampipe PostgreSQL Password : \033[0minit_password"' >> ~/.bashrc \
 && echo -e '\necho -e "\n\033[1;34m[Description : Command] Get Password From Steampipe : \033[0m\$password"' >> ~/.bashrc \
 && echo -e '\necho -e "\n\033[1;34m[Description : Command] Run Python Module : \033[0mpython __init__.py \$password\n"' >> ~/.bashrc \
 && steampipe plugin install steampipe aws \
 && sudo mkdir -p output/raw_data \
 && sudo chmod 777 output/raw_data
