#!/bin/bash

read -p "SSO Session Name [hanwhavision]: " SSO_SESSION_NAME
SSO_SESSION_NAME=${SSO_SESSION_NAME:-hanwhavision}
read -p "SSO Start URL [https://htaic.awsapps.com/start]: " SSO_URL
SSO_URL=${SSO_URL:-https://htaic.awsapps.com/start}
read -p "SSO Region [us-west-2]: " SSO_REGION
SSO_REGION=${SSO_REGION:-us-west-2}
read -p "AWS Profile Default Region [us-east-1]: " REGION
REGION=${REGION:-us-east-1}
sudo mkdir -p /home/steampipe/.aws
sudo chown -R steampipe:steampipe /home/steampipe/.aws
tee /home/steampipe/.aws/config > /dev/null <<EOT
[sso-session $SSO_SESSION_NAME]
sso_start_url = $SSO_URL
sso_region = $SSO_REGION
sso_registration_scopes = sso:account:access
EOT

# AWS SSO Session Login
aws sso login --sso-session $SSO_SESSION_NAME

# Get the latest access token
access_token=$(cat ~/.aws/sso/cache/$(ls -t ~/.aws/sso/cache | head -n 1) | jq -r '.accessToken')

# Check if access_token is valid
if [ -z "$access_token" ]; then
    echo "Error: Access token not found. Please ensure you are logged into SSO."
    exit 1
fi

# Retrieve the list of AWS accounts and check for errors
accounts_json=$(aws sso list-accounts --access-token "$access_token" --region "$SSO_REGION" --output json 2>/dev/null)

# Verify if the accounts_json variable is populated and valid JSON
if [ -z "$accounts_json" ] || ! echo "$accounts_json" | jq . >/dev/null 2>&1; then
    echo "Error: Failed to retrieve the account list. Check the access token or SSO configuration."
    exit 1
fi

# Parse account list with jq
accounts=$(echo "$accounts_json" | jq -c '.accountList[]')

# Loop through each account and configure profile
echo "$accounts_json" | jq -c '.accountList[]' | while read -r account; do
    account_id=$(echo "$account" | jq -r '.accountId')
    full_account_name=$(echo "$account" | jq -r '.accountName')
    account_name=$(echo "$full_account_name" | awk '{print $NF}')
    if [ -z "$account_id" ] || [ -z "$account_name" ]; then
        echo "Error: Failed to retrieve account_id or account_name for account: $account"
        continue
    fi

    roles_json=$(aws sso list-account-roles --account-id "$account_id" --access-token "$access_token" --region "$SSO_REGION" --output json 2>/dev/null)

    if [ -z "$roles_json" ] || ! echo "$roles_json" | jq . >/dev/null 2>&1; then
        echo "Error: Failed to retrieve roles for account_id: $account_id"
        continue
    fi

    profile_name="${account_name//-/_}"
    roles=$(echo "$roles_json" | jq -c '.roleList[]')

    for role in $roles; do
        role_name=$(echo "$role" | jq -r '.roleName')

        aws configure set profile."$profile_name".sso_session "$SSO_SESSION_NAME"
        aws configure set profile."$profile_name".sso_account_id "$account_id"
        aws configure set profile."$profile_name".sso_role_name "$role_name"
        aws configure set profile."$profile_name".region "$REGION"
	aws configure set profile."$profile_name".output "json"

	echo "> Profile configured: { ProfileName: $profile_name, AccountId: $account_id, RoleName: $role_name" }
    done
done

# Define the input and output files
input_file="/home/steampipe/.aws/config"
output_file="/home/steampipe/.steampipe/config/aws.spc"
# Clear the output file if it exists
> "$output_file"
# Read each profile block from the input file
while read -r line; do
    # Check if the line starts with [profile
    if [[ $line == [profile* ]]; then
        # Extract the profile name by removing the "[profile " and "]"
        profile_name=$(echo "$line" | sed 's/\[profile //; s/\]//')

        # Append the new format to the output file
        {
            echo "connection \"$profile_name\" {"
            echo "  plugin = \"aws\""
            echo "  profile = \"$profile_name\""
            echo "  regions = [\"us-east-1\"]"  # Adjust the default region as needed
            echo "}"
        } >> "$output_file"
    fi
done < "$input_file"
