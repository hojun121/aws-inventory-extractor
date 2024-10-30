<p align="center">
  <img src="https://github.com/user-attachments/assets/08ed8337-916c-4ae7-8c1c-66d26ff85329" alt="AWS Resource Inventory Extractor">
</p>

# AWS Resource Inventory Extractor

A module that uses awscli and the open-source tool Steampipe to extract AWS resources and export them to a structured inventory file.

This module supports a total of three modes.

- Extract pre-procesing inventory mode
  - VPC, VPC Endpoint, Peering Connection
  - Transit Gateway
  - Subnet
  - Security Groups
  - Network ACLs
  - EC2
  - ELB
  - Target Group
  - Auto Scaling
  - ElastiCache
  - CloudFront
  - S3
  - IAM Group, Role, User
  - RDS, DocumentDB

- Extract raw-data inventory mode
  - All active AWS resources

- Connect [Steampipe Query](https://steampipe.io/docs/query/query-shell) (In-Memory PostgreSQL Interface Tool) mode
  - Connect to In-MemoryDB

## Tech Stack
- [Steampipe wit aws plugin (Opensorce)](https://hub.steampipe.io/plugins/turbot/aws)
- awscli
- postgresql schema parser (In-house developed python code): v1.0.2

## Pre-requirements
- For fater extraction, 2 vCpu & 8 Ram are recommended
- Docker version: v27.3.1
- AWS Account: Read-Only Permissions (to security)
- Steampipe Config

## Execution Guide
### [ Prod Env ]
#### Dockerfile Build
```bash
docker build -t {{imageName}} .
```
#### Container Run
```bash
docker run --rm -it -v {{Your Host Directory}}:/app/inventory {{imageName}}
```
### [ Dev Env ]
#### Dockerfile Build
```bash
cd python
docker build -f Dockerfile -t {{dev-imageName}} .
```
#### Container Run
```bash
docker run -itd --name {{dev-containerName}} -v {{Your Host Directory}}:/app/inventory {{dev-imageName}}
```
#### Container exec
```bash
docker exec -it {{dev-containerName}} bash
```

## Steps of Operation
### [ 1 / 5 ] Authenticate with AWS using awscli: IAM or SSO.

- IAM Login
  - Input the below data to IAM login.
    ```
    AWS Access Key ID : (Your IAM user's Access Key ID here.)
    AWS Secret Access Key : (Your IAM user's Secret Access Key here.)
    Default region name : (Your Project Region)
    Default output format :json 
    ```

- SSO Login
  - Input the below data to SSO login.
    ```
    SSO session name (hanwhavision): (Your SSO Session Name, Default: hanwhavision)
    SSO start URL [https://htaic.awsapps.com/start]: (Your SSO URL, Default: https://htaic.awsapps.com/start)
    SSO region [us-west-2]: (Your SSO Region, Default: us-west-2)
    ```
  - Open the following URL and enter the given code.
    
    ![image](https://github.com/user-attachments/assets/ade9aa67-a885-4117-ad52-375ae7ec55be)
  
  - After SSO login, allow access.
  
    ![image](https://github.com/user-attachments/assets/dd72cd0d-7060-45fb-8ae0-bf3b8f52967e)

  - Select AWS Account Profile Config Setup Method.
 
    ![image](https://github.com/user-attachments/assets/e1ab1526-2eee-460e-9767-ac40c85fc8ac)
    - Auto: Extract SSO Accounts Profile Automatically, **you should inpit Default Region**.
    - Manual: Copy & Paste AWS Profile Context.
      ![image](https://github.com/user-attachments/assets/267737a0-c0db-46d4-8303-5ed6c7f04635)

       

### [ 2 / 5 ] Setup Steampipe config file.
- This module extracts AWS resources according to the default region configured in IAM.

### [ 3 / 5 ] Extract AWS resources into an in-memory PostgreSQL.
- If all the above steps are completed successfully, extracting AWS resources into an in-memory PostgreSQL database will function properly.

  ![image](https://github.com/user-attachments/assets/15e94696-beb0-4c10-ad6e-9d9f3121d27b)

### [ 4 / 5 ] Select desired Mode.
- If you select Pre-processing or Raw-data mode, than go to step 5.
- If you select Steampipe Query, than conn to DB Session.

### [ 5 / 5 ] Extract an in-memory postgreSQL to structured inventory file.
- The inventory file(s) will be successfully created in the inventory volume.
