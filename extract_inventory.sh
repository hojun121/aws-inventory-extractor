#!/bin/bash

# Display menu for selecting login method
echo "[1/4] Select your AWS login method:"
echo "1) IAM"
echo "2) SSO"
read -p "Enter the number (1 or 2): " login_choice

# Process the selected login method
if [ "$login_choice" -eq 1 ]; then
    echo "You selected IAM."
    # Run AWS configure for IAM login
    aws configure

    if aws sts get-caller-identity > /dev/null 2>&1; then
        echo "AWS login successful!"
    else
        echo "AWS login failed. Please check your credentials or configuration."
        exit 1
    fi

elif [ "$login_choice" -eq 2 ]; then
    echo "You selected SSO."
    aws configure sso
    echo "\nPlease input the aws config to overwrite ~/.aws/config (Press Ctrl+D when done):"
    cat > /home/steampipe/.aws/config <<EOF
$(cat)
EOF
    cat <<EOT >> /home/steampipe/.aws/config
[sso-session hanwhavision]
sso_start_url = https://htaic.awsapps.com/start
sso_region = us-west-2
sso_registration_scopes = sso:account:access
EOT

else
    echo "Invalid selection. Exiting..."
    exit 1
fi

echo "\n[2/4] Please input the config to overwrite ~/.steampipe/config/aws.spc (Press Ctrl+D when done):"
cat > /home/steampipe/.steampipe/config/aws.spc <<EOF
$(cat)
EOF
echo "\nThe file ~/.steampipe/config/aws.spc has been updated."

echo "\n[3/4] Starting the process of extracting AWS resources into an in-memory PostgreSQL."
password=$(steampipe service start --show-password | grep 'Password:' | awk '{print $2}')
echo "Extracting AWS resources into an in-memory PostgreSQL successful!"

echo "\n[4/4] Starting the process of extracting an in-memory PostgreSQL to structured inventory file."
i=5
while [ $i -gt 0 ]
do
    echo "Starting in $i seconds..."
    sleep 1
    i=$((i-1))
done

/app/runable_python_binary "$password"
