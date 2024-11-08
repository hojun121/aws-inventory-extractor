import boto3
import pandas as pd
import json
import os
import re
import sys
import multiprocessing
from datetime import datetime
from modules.asg import list_auto_scaling_groups
from modules.cloudfront import list_cloudfront_distributions
from modules.ec2 import list_ec2_instances
from modules.elasticache import list_elasticache_clusters
from modules.elb import list_elbs
from modules.iamrole import list_iam_roles
from modules.nacl import list_nacls
from modules.db import list_db_clusters
from modules.s3 import list_s3_buckets
from modules.sg import list_security_groups
from modules.subnet import list_subnets
from modules.tg import list_target_groups
from modules.vpc import list_vpcs
from botocore.exceptions import BotoCoreError, ClientError, ProfileNotFound, NoCredentialsError
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import Alignment, PatternFill
from tqdm import tqdm

def write_dataframes_to_excel(dataframes, profile_name):
    if not dataframes:
        print("No data available to write to Excel.")
        return

    current_date = datetime.now().strftime('%y_%m_%d')
    file_name = f"[{profile_name}]_inventory_{current_date}.xlsx"
    file_name_with_dir = f"/app/output/{file_name}"
    os.makedirs(os.path.dirname(file_name_with_dir), exist_ok=True)

    try:
        with pd.ExcelWriter(file_name_with_dir) as writer:
            for sheet_name, df in dataframes.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)

        # Adjust column width, center align cells, add header color, and enable filter
        workbook = load_workbook(file_name_with_dir)
        header_fill = PatternFill(start_color='FFFFCC', end_color='FFFFCC', fill_type='solid')
        for sheet_name in workbook.sheetnames:
            worksheet = workbook[sheet_name]
            for cell in worksheet[1]:
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal='center', vertical='center')
            worksheet.auto_filter.ref = worksheet.dimensions
            for column in worksheet.columns:
                max_length = max(len(str(cell.value)) for cell in column if cell.value) + 2
                column_letter = get_column_letter(column[0].column)
                worksheet.column_dimensions[column_letter].width = max_length
                for cell in column:
                    cell.alignment = Alignment(horizontal='center', vertical='center')
        workbook.save(file_name_with_dir)

        print(f"[{profile_name}] Inventory creation successful => {file_name}")
    except Exception as e:
        print(f"Error writing data to Excel: {e}")

def list_all_resources(session, profile_name):
    resource_functions = [
        (list_vpcs, 'VPCs'),
        (list_subnets, 'Subnets'),
        (list_security_groups, 'Security Groups'),
        (list_nacls, 'Nacl'),
        (list_ec2_instances, 'EC2 Instances'),
        (list_auto_scaling_groups, 'Auto Scaling Groups'),
        (list_elbs, 'Load Balancers'),
        (list_target_groups, 'Target Groups'),
        (list_cloudfront_distributions, 'CloudFront Distributions'),
        (list_s3_buckets, 'S3 Buckets'),
        (list_iam_roles, 'IAM Roles'),
        (list_db_clusters, 'Database'),
        (list_elasticache_clusters, 'ElastiCache Clusters')
    ]

    dataframes = {}
    for func, sheet_name in tqdm(resource_functions, desc=f"[{profile_name}] Inventory creation in progress", unit="resource"):
        try:
            data = func(session)
            if data:
                dataframes[sheet_name] = pd.DataFrame(data)
        except Exception as e:
            print(f"\nError retrieving data for {sheet_name}: {e}")

    write_dataframes_to_excel(dataframes, profile_name)

def create_boto3_session(profile_name):
    try:
        session = boto3.Session(profile_name=profile_name)
        return session
    except ProfileNotFound:
        print(f"AWS profile '{profile_name}' not found. Please check your AWS configuration.")
    except NoCredentialsError:
        print("AWS credentials not found. Please check your AWS configuration.")
    return None

def single_inventory_maker(profile_name):
    session = create_boto3_session(profile_name)
    if session:
        list_all_resources(session, profile_name)
    else:
        print(f"[{profile_name}] Session is something wrong..")

def multi_inventory_maker(profile_names):
    print(f"### Total AWS Profiles: {len(profile_names)} ###")
    # Get the number of CPU cores in the system
    num_cores = multiprocessing.cpu_count()
    print("This module simultaneously extract AWS profile inventories using the available number of cores.")
    print(f"Currently available number of CPU cores: {num_cores}")

    # Perform multiprocessing based on profile names using Pool
    with multiprocessing.Pool(num_cores) as pool:
        pool.map(single_inventory_maker, profile_names)

def get_aws_profiles(aws_config_path):
    config_path = os.path.expanduser(aws_config_path)
    if not os.path.exists(config_path):
        print(f"Config file not found at {config_path}")
        sys.exit(1)

    with open(config_path, 'r') as file:
        config_content = file.read()
        profiles = re.findall(r'\[profile (.*?)\]', config_content)
        return profiles

if __name__ == "__main__":
    # Get AWS profile names
    profile_names = get_aws_profiles("~/.aws/config")
    if profile_names:
        multi_inventory_maker(profile_names)
    else:
        single_inventory_maker("default")

    
