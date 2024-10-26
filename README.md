# AWS Resource Inventory Extractor 

A module that uses awscli and the open-source tool Steampipe to extract AWS resources and export them to a structured inventory file.

You can verify the explaination on [Detail Documantation(Jira Confluence)](https://hanwhavision.atlassian.net/wiki/x/T4KKK).

## Tech Stack
- [Steampipe wit aws plugin (Opensorce)](https://hub.steampipe.io/plugins/turbot/aws)
- awscli
- postgresql schema parser (In-house developed python code)

## Steps of Operation
- [1/4] Authenticate with AWS using awscli: IAM or SSO.
- [2/4] Setup Steampipe config file.
- [3/4] Extract AWS resources into an in-memory PostgreSQL.
- [4/4] Extract an in-memory PostgreSQL to structured inventory file.

## Pre-requirements
- For fater extraction, 2 vCpu & 8 Ram are recommended
- Docker version: v24.0.5
- AWS Account
- Steampipe Config

## Execution Guide
### [ Prod Env ]
#### Dockerfile Build
```bash
docker build -t {{imageName}} .
```
#### Container Run
```bash
docker run --rm -it -v {{Your Host Directory}}:/app/inventory {{imageName}} sh extract_inventory.sh
```
### [ Dev Env ]
#### Dockerfile Build
```bash
docker build -f Dockerfile-dev -t {{dev-imageName}} .
```
#### Container Run
```bash
docker run -itd --name {{dev-containerName}} -v {{Your Host Directory}}:/app/inventory {{dev-imageName}}
```
#### Container exec
```bash
docker exec -it {{dev-containerName}} bash
```


The extracted inventory will be created in {{Your Host Directory}}.
