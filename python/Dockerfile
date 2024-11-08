FROM ubuntu:22.04 AS builder
# Install necessary dependencies
WORKDIR /app
COPY . .
RUN apt-get update -y \
 && apt-get install -y sudo build-essential libpq-dev python3 python3-pip sudo curl less unzip apt-utils vim jq \
 && pip install -r requirements.txt \
 && sudo ln -s /usr/bin/python3 /usr/bin/python \
 && export PATH=$PATH:~/.local/bin \
 && curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
 && unzip awscliv2.zip \
 && ./aws/install \
 && rm -rf awscliv2.zip aws/ \
 && echo 'init_sso() {' >> ~/.bashrc \
 && echo '    echo "SetUp AWS SSO Config"' >> ~/.bashrc \
 && echo '    /app/configure_aws.sh' >> ~/.bashrc \
 && echo '    echo "Check ~/.aws/config"' >> ~/.bashrc \
 && echo '}' >> ~/.bashrc \
 && echo 'cmd() {' >> ~/.bashrc \
 && echo '    source ~/.bashrc' >> ~/.bashrc \
 && echo '}' >> ~/.bashrc \
 && echo 'echo "[Pre-Requirement] You should run init_sso first to ensure AWS login"' >> ~/.bashrc \
 && echo 'echo "[Description : Command] Help Command : cmd"' >> ~/.bashrc \
 && echo 'echo "[Description : Command] AWS IAM Login : aws configure"' >> ~/.bashrc \
 && echo 'echo "[Description : Command] AWS SSO Initialize : init_sso"' >> ~/.bashrc \
 && echo 'echo "[Description : Command] Run Python Module : python __init__.py"' >> ~/.bashrc \
 && sudo chmod 777 configure_aws.sh