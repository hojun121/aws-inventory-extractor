# AWS Resource Inventory Extractor

- A Module that uses AWSCLI to Extract AWS Resources and Export Them to a Structured Inventory Files.

<p align="center">
  <img src="https://github.com/user-attachments/assets/08ed8337-916c-4ae7-8c1c-66d26ff85329" alt="AWS Resource Inventory Extractor">
</p>

## Tech Stack
- AWSCLI Latest
- Python 3.10
- Ubuntu 22.04

## Pre-requirements
- 2 vCPU / 8 RAM
- Docker Version >= v24.0.2
- SSO Auth: Read-Only Permissions (to security)

## Currently Extractable 3 Items

- ( 1 / 3 ) Inventory file

  ```
  Virtual Private Cloud (VPC)
  Subnet
  Elastic Kubernetes Service (EKS)
  Auto Scaling Group (ASG)
  Elastic Compute Cloud (EC2)
  Security Group
  Network ACL (NACL)
  Elastic Load Balancer (ELB)
  Load Balancer Target Group
  Relational Database Service (RDS)
  DynamoDB
  ElastiCache
  Managed Streaming for Apache Kafka (MSK)
  OpenSearch Service
  Route 53
  CloudFront
  Simple Storage Service (S3)
  Lambda
  Certificate Manager (ACM)
  Key Management Service (KMS)
  Secrets Manager
  Simple Queue Service (SQS)
  Simple Email Service (SES)
  Simple Notification Service (SNS)
  
  ```
- ( 2 / 3 ) Security Group Detailed Analysis File
- ( 3 / 3 ) Route53 Detailed Analysis File

For additional items, please send a request to jaeho.p@hanwha.com

## Usage Guide

### [ 1 / 3 ] Run the Container in One of Two Ways.

#### Container Run (or Build and Run the Image Manually)
```bash
docker run -it --name hanwha_inventory -p 5000:5000 hojun121/hanwha_inventory:v2.0.0
```
```bash
docker build -t {{imageName}} . && docker run -it --name {{container_name}} -p 5000:5000 {{imageName}}
```

### [ 2 / 3 ] After Starting the Container, Generate the SSO Session Metadata, Login

#### SSO Login
- Input the Below Data to SSO Login. (Simply Press Enter to Use the Default Value)
  ```
  SSO session name [hanwhavision]: 
  SSO start URL [https://htaic.awsapps.com/start]: 
  SSO region [us-west-2]: 
  ```
- Open the Following URL and Enter the Given Code.
  
  ![image](https://github.com/user-attachments/assets/ade9aa67-a885-4117-ad52-375ae7ec55be)

- After SSO Login, Allow Access.

  ![image](https://github.com/user-attachments/assets/dd72cd0d-7060-45fb-8ae0-bf3b8f52967e)

#### The Profiles of AWS Accounts Accessible are Automatically Saved Inside the Container.

- The internal configuration is completed automatically.

  ![overall_screen](https://github.com/user-attachments/assets/6df6ffb2-71cb-408e-8d36-43f9ba256508)

### [ 3 / 3 ] Access the Inventory Dashboard

- It Runs on Port 5000 (localhost:5000)

  ![Dashboard](https://github.com/user-attachments/assets/7fc0503f-e85c-4973-ad03-c178b2a27007)

### [ Exception ] The SSO Session Expires, You Need to Restart the Container to Login to SSO Again.
  
  ![exception](https://github.com/user-attachments/assets/b49e42fd-b034-4207-a6df-5cfc228eb894)

#### Container Restart
```bash
docker stop {{container_name}} && docker start -ai {{container_name}}
```
