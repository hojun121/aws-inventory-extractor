#!/bin/bash
clear
export PATH=$PATH:/usr/games

# Display welcome message
cowsay -f dragon "Welcome to Hanwha AWS Inventory World!" | lolcat

### [Step 1] SSO Login Configuration ###
echo ""
echo "[Step 1/4] AWS SSO Login Configuration" | lolcat
echo ""

mkdir -p ~/.aws

# Check if sso-session already exists
if grep -q "^\[sso-session hanwhavision\]" ~/.aws/config 2>/dev/null; then
    echo "AWS sso-session config already exist. Skipping config setup." 
    # If found, use default values (hardcoded or load from file if needed)
    SSO_SESSION_NAME="hanwhavision"
    SSO_URL="https://htaic.awsapps.com/start"
    SSO_REGION="us-west-2"
    DEFAULT_REGION="us-east-1"
else
    # Prompt for input
    read -p "SSO Session Name [hanwhavision]: " SSO_SESSION_NAME
    SSO_SESSION_NAME=${SSO_SESSION_NAME:-hanwhavision}

    read -p "SSO Start URL [https://htaic.awsapps.com/start]: " SSO_URL
    SSO_URL=${SSO_URL:-https://htaic.awsapps.com/start}

    read -p "SSO Region [us-west-2]: " SSO_REGION
    SSO_REGION=${SSO_REGION:-us-west-2}

    read -p "AWS Profile Default Region [us-east-1]: " DEFAULT_REGION
    DEFAULT_REGION=${DEFAULT_REGION:-us-east-1}

    # Write config only if it didn't exist
    tee -a ~/.aws/config > /dev/null <<EOT
[sso-session $SSO_SESSION_NAME]
sso_start_url = $SSO_URL
sso_region = $SSO_REGION
sso_registration_scopes = sso:account:access

EOT
fi

# [Step 2] AWS SSO Login
echo ""
echo "[Step 2/4] AWS SSO Login" | lolcat
echo ""

IS_CONTAINER=${IS_CONTAINER:-false} 

if [ "$IS_CONTAINER" = "true" ]; then
    aws sso login --sso-session "$SSO_SESSION_NAME" --use-device-code
else
    aws sso login --sso-session "$SSO_SESSION_NAME"
fi

### [Step 3] AWS Account Profile Setup ###
echo ""
echo "[Step 3/4] AWS Account Profiles Setup" | lolcat
echo ""
# Check if profiles already exist
if grep -q "^\[profile " ~/.aws/config 2>/dev/null; then
    echo "AWS profiles already exist. Skipping profile setup."
else
    echo "No AWS profiles found. Creating profiles..."

    # Get the latest SSO access token
    access_token=$(cat ~/.aws/sso/cache/$(ls -t ~/.aws/sso/cache | head -n 1) | jq -r '.accessToken')

    if [ -z "$access_token" ]; then
        echo "Error: Access token not found. Please login again."
        exit 1
    fi

    # Retrieve AWS account list
    accounts_json=$(aws sso list-accounts --access-token "$access_token" --region "$SSO_REGION" --output json 2>/dev/null)

    if [ -z "$accounts_json" ] || ! echo "$accounts_json" | jq . >/dev/null 2>&1; then
        echo "Error: Failed to retrieve account list. Check your SSO login."
        exit 1
    fi

    # Loop over each account and configure profile
    echo "$accounts_json" | jq -c '.accountList[]' | while read -r account; do
        account_id=$(echo "$account" | jq -r '.accountId')
        full_account_name=$(echo "$account" | jq -r '.accountName')
        profile_name=$(echo "$full_account_name" | sed 's/[ -]/_/g' | tr '[:upper:]' '[:lower:]')

        roles_json=$(aws sso list-account-roles --account-id "$account_id" --access-token "$access_token" --region "$SSO_REGION" --output json 2>/dev/null)

        if [ -z "$roles_json" ] || ! echo "$roles_json" | jq . >/dev/null 2>&1; then
            echo "Error: Failed to retrieve roles for account: $full_account_name"
            continue
        fi

        echo "$roles_json" | jq -c '.roleList[]' | while read -r role; do
            role_name=$(echo "$role" | jq -r '.roleName')

            aws configure set profile."$profile_name".sso_session "$SSO_SESSION_NAME"
            aws configure set profile."$profile_name".sso_account_id "$account_id"
            aws configure set profile."$profile_name".sso_role_name "$role_name"
            aws configure set profile."$profile_name".region "$DEFAULT_REGION"
            aws configure set profile."$profile_name".output "json"

            echo "> Profile configured: { ProfileName: $profile_name, AccountId: $account_id, RoleName: $role_name }" | lolcat
        done
    done
fi

### [Step 4] Run Inventory Flask App ###
echo ""
echo "[Step 4/4] Running AWS Inventory Flask App" | lolcat
echo ""

# Countdown before running the binary
for i in {5..1}; do
    echo -n "Starting" | lolcat
    echo -n " in "
    echo -n "$i" | lolcat
    echo " seconds..."
    sleep 1
done
# Completion message
cowsay -f turtle "The AWS Inventory Web Start!" | lolcat

# Execute the inventory binary (actual resource extraction)
if [ "$IS_CONTAINER" = "true" ]; then
    /app/inventory_binary
else
    python ./python/app.py
fi
