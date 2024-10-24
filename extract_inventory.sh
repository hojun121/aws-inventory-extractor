#!/bin/bash
clear
export PATH=$PATH:/usr/games
cowsay -f dragon "Welcome to AWS Resource Extractor!" | lolcat
# Display menu for selecting login method
echo -e "\033[1;33m[1/5] Select your AWS login method\033[0m"
echo -e "\033[1;34m(1) IAM\033[0m"
echo -e "\033[1;34m(2) SSO\033[0m"
read -p "Enter the number (1 or 2): " login_choice

# Step 1
# Process the selected login method
if [ "$login_choice" -eq 1 ]; then
    echo -e "\033[1;34mYou selected IAM.\033[0m"
    # Run AWS configure for IAM login
    aws configure

    if aws sts get-caller-identity > /dev/null 2>&1; then
        echo -e "\033[1;32mAWS login successful!\033[0m"
    else
        echo -e "\033[1;31mAWS login failed. Please check your credentials or configuration.\033[0m"
        exit 1
    fi

elif [ "$login_choice" -eq 2 ]; then
    echo -e "\033[1;34mYou selected SSO.\033[0m"
    aws configure sso
    echo -e "\n\033[1;34mPlease input the aws config to overwrite ~/.aws/config (Press Ctrl+D when done)\033[0m"
    cat > /home/steampipe/.aws/config <<EOF
$(cat)
EOF
    cat <<EOT >> /home/steampipe/.aws/config
[sso-session hanwhavision]
sso_start_url = https://htaic.awsapps.com/start
sso_region = us-west-2
sso_registration_scopes = sso:account:access
EOT
echo -e "\n\033[1;32mThe file ~/.aws/config has been updated.\033[0m"
else
    echo -e "\033[1;31mInvalid selection. Please enter a number. Exiting...\033[0m"
    exit 1
fi

# Step 2
echo -e "\n\033[1;33m[2/5] Please input the config to overwrite ~/.steampipe/config/aws.spc (Press Ctrl+D when done)\033[0m"

if [[ "$login_choice" == "1" ]]; then
    echo -e "\n\033[1;32mThe IAM login Method Skips This Process.\033[0m"
elif [[ "$login_choice" == "2" ]]; then
    cat > /home/steampipe/.steampipe/config/aws.spc <<EOF
$(cat)
EOF
    echo -e "\n\033[1;32mThe file ~/.steampipe/config/aws.spc has been updated.\033[0m"
fi

# Step 3
echo -e "\n\033[1;33m[3/5] Starting the process of extracting AWS resources into an In-Memory PostgreSQL.\033[0m"
echo -e "\033[1;34mExtracting AWS resources into an In-Memory PostgreSQL database is in progress...\033[0m"
password=$(steampipe service start --show-password | grep 'Password:' | awk '{print $2}')
echo -e "\033[1;32mExtracting AWS resources into an In-Memory PostgreSQL is successful!\033[0m"

# Step 4
echo -e "\n\033[1;33m[4/5] Please select your desired mode.\033[0m"
echo -e "\033[1;34m(1) Extract Pre-Procesing Inventory\033[0m"
echo -e "\033[1;34m(2) Extract Raw-Data Inventory\033[0m"
echo -e "\033[1;34m(3) Connect Steampipe Query (In-Memory PostgreSQL Interface Tool)\033[0m"
read -p "Enter the number (1 or 2 or 3): " mode_choice

# step 5
echo -e "\n\033[1;33m[5/5] Starting the Selected Mode\033[0m"
i=5
while [ $i -gt 0 ]
do
    echo "Starting in $i seconds..." | lolcat
    sleep 1
    i=$((i-1))
done

if [[ "$mode_choice" == "1" ]]; then
    echo -e "\n\033[1;33mExtracting from In-Memory PostgreSQL to Pre-processing Inventory file...\033[0m"
    /app/pre_processor_binary "$password"
    cowsay -f turtle "AWS Inventory Extraction is done. Please Confirm Your Inventorys!" | lolcat
elif [[ "$mode_choice" == "2" ]]; then
    echo -e "\n\033[1;33mExtracting from In-Memory PostgreSQL to Raw-Data Inventory file...\033[0m"
    /app/pre_processor_binary "$password"
    cowsay -f turtle "AWS Inventory Extraction is done. Please Confirm Your Inventorys!" | lolcat
elif [[ "$mode_choice" == "3" ]]; then
    echo -e "\033[1;34m\n==========================================================\033[0m"
    echo -e "\033[1;34mHelpful Links: https://steampipe.io/docs/query/query-shell\033[0m"
    echo -e "\033[1;34mYou can exit the query shell by pressing Ctrl+d on a blank line, or using the .exit command.\033[0m"
    echo -e "\033[1;34m==========================================================\n\033[0m"
    steampipe query
    cowsay -f turtle "Good-Bye!" | lolcat
else
    echo "Invalid choice. Please enter 1, 2, or 3."
fi
