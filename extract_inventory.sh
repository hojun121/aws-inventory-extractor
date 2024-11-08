#!/bin/sh
clear
export PATH=$PATH:/usr/games
cowsay -f dragon "Welcome to AWS Resource Extractor!" | lolcat

# Display menu for selecting login method
echo "\033[1;33m[1/2] Select your AWS login method\033[0m"
echo "\033[1;34m(1) IAM\033[0m"
echo "\033[1;34m(2) SSO\033[0m"
read -p "Enter the number (1 or 2): " login_choice

####### Step 1
# Process the selected login method
if [ "$login_choice" = "1" ]; then
    echo "\033[1;34mYou selected IAM.\033[0m"
    aws configure

    if aws sts get-caller-identity > /dev/null 2>&1; then
        echo "\033[1;32mAWS login successful!\033[0m"
    else
        echo "\033[1;31mAWS login failed. Please check your credentials or configuration.\033[0m"
        exit 1
    fi

elif [ "$login_choice" = "2" ]; then
    echo "\033[1;34mYou selected SSO.\033[0m"
    printf "SSO Session Name [hanwhavision]: "
    read SSO_SESSION_NAME
    SSO_SESSION_NAME=${SSO_SESSION_NAME:-hanwhavision}
    printf "SSO Start URL [https://htaic.awsapps.com/start]: "
    read SSO_URL
    SSO_URL=${SSO_URL:-https://htaic.awsapps.com/start}
    printf "SSO Region [us-west-2]: "
    read SSO_REGION
    SSO_REGION=${SSO_REGION:-us-west-2}
    echo "\033[1;34mInput the AWS Account Default Region.\033[0m"
    printf "Default Region [us-east-1]: "
    read DEFAULT_REGION
    DEFAULT_REGION=${DEFAULT_REGION:-us-east-1}
    mkdir -p /root/.aws
    tee /root/.aws/config > /dev/null <<EOT
[sso-session $SSO_SESSION_NAME]
sso_start_url = $SSO_URL
sso_region = $SSO_REGION
sso_registration_scopes = sso:account:access
EOT
    echo ""
    # AWS SSO Session Login
    aws sso login --sso-session "$SSO_SESSION_NAME"

    echo "\n\033[1;34mSelect AWS Account Profile Config Setup Method.\033[0m"
    echo "\033[1;34m(1) Auto: The region for all AWS account profiles is set to Same Region(Default Region).\033[0m"
    echo "\033[1;34m(2) Manual: Each account can freely set its own region.\033[0m"
    read -p "Enter the number (1 or 2): " PROFILE_CHOICE

    if [ "$PROFILE_CHOICE" = "1" ]; then
        printf "Auto mode selected."
        echo "\n\033[1;32mSetting all account profiles to default region: $DEFAULT_REGION.\033[0m\n"

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
            profile_name=$(echo "$account_name" | sed 's/-/_/g')
            roles=$(echo "$roles_json" | jq -c '.roleList[]')
            echo "$roles" | while read -r role; do
                role_name=$(echo "$role" | jq -r '.roleName')

                aws configure set profile."$profile_name".sso_session "$SSO_SESSION_NAME"
                aws configure set profile."$profile_name".sso_account_id "$account_id"
                aws configure set profile."$profile_name".sso_role_name "$role_name"
                aws configure set profile."$profile_name".region "$DEFAULT_REGION"
                aws configure set profile."$profile_name".output "json"

                echo "> Profile configured: { ProfileName: $profile_name, AccountId: $account_id, RoleName: $role_name }" | lolcat
            done
        done

    elif [ "$PROFILE_CHOICE" = "2" ]; then
        echo "\033[1;32mManual mode selected. You can set the region for each account profile.\033[0m"
        echo "\033[0;36m~/.aws/config File Format\033[0m"
        echo "\033[0;36m[profile {{project_1 profile name}}]\033[0m"
        echo "\033[0;36msso_session = {{SSO Session name}}\033[0m"
        echo "\033[0;36msso_account_id = {{project_1 AWS Account}}\033[0m"
        echo "\033[0;36msso_role_name = {{Your role name}}\033[0m"
        echo "\033[0;36mregion = us-east-1\033[0m"
        echo "\033[0;36moutput = json\033[0m"
        echo "\033[0;36m[profile {{project_2 profile name}}]\033[0m"
        echo "\033[0;36msso_session = {{SSO Session name}}\033[0m"
        echo "\033[0;36msso_account_id = {{project_2 AWS Account}}\033[0m"
        echo "\033[0;36msso_role_name = {{Your role name}}\033[0m"
        echo "\033[0;36mregion = us-east-1\033[0m"
        echo "\033[0;36moutput = json\033[0m"
        echo "\033[0;36m...\033[0m"

        echo "\n\033[1;34mPlease input the aws config to overwrite ~/.aws/config (Press Ctrl+D when done)\033[0m"
        cat >> /root/.aws/config
    else
        echo "\033[1;31mInvalid choice. Please enter 1 or 2.\033[0m"
        exit 1
    fi

    echo "\n\033[1;32mThe AWS Profile Config has been Setup.\033[0m"
else
    echo "\033[1;31mInvalid selection. Please enter a number. Exiting...\033[0m"
    exit 1
fi

####### Step 2
echo "\n\033[1;33m[2/2] AWS Inventory Creation\033[0m"
i=5
while [ $i -gt 0 ]; do
    echo "Starting in $i seconds..." | lolcat
    sleep 1
    i=$((i-1))
done

/app/inventory_binary
cowsay -f turtle "AWS Inventory Extraction is done. Please Confirm Your Inventorys!" | lolcat
