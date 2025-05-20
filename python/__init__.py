import boto3
import pandas as pd
import json
import os
import re
import sys
import subprocess
import multiprocessing
from datetime import datetime
from modules.msk import list_kafka_clusters
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

temporary_path="/app/output/"
inventory_path='/app/inventory'

def workbook_with_format(file_name_with_dir):
    try:
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
        if os.path.isdir(inventory_path):
            subprocess.run(['cp', file_name_with_dir, inventory_path], check=True)
    except Exception as e:
        return e

def write_dataframes_to_excel(dataframes, profile_name):
    if not dataframes:
        print("No data available to write to Excel.")
        return

    current_date = datetime.now().strftime('%y_%m_%d')
    file_name = f"{profile_name}_inventory_{current_date}.xlsx"
    file_name_with_dir = f"{temporary_path}{file_name}"
    os.makedirs(os.path.dirname(file_name_with_dir), exist_ok=True)

    try:
        with pd.ExcelWriter(file_name_with_dir) as writer:
            for sheet_name, df in dataframes.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)

        workbook_with_format(file_name_with_dir)
        print(f"{profile_name} Inventory creation successful => {file_name}")
        
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
        (list_cloudfront_distributions, 'CloudFront'),
        (list_s3_buckets, 'S3'),
        (list_iam_roles, 'IAM Roles'),
        (list_db_clusters, 'Database'),
        (list_elasticache_clusters, 'ElastiCache'),
        (list_kafka_clusters, 'MSK')
    ]

    dataframes = {}
    for func, sheet_name in tqdm(resource_functions, desc=f"{profile_name} Inventory creation in progress", unit="resource"):
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
        print(f"{profile_name} Session is something wrong..")

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

# Function to extract data from Excel files
def netrix_maker():
    # List to store data
    data_list = []

    # Iterate through all files in the directory
    for filename in os.listdir(temporary_path):
        # Check if the filename matches the pattern
        if filename.endswith(".xlsx") and "_inventory_" in filename:
            try:
                # Extract account name from filename
                account_name = filename.split('_inventory_')[0].strip('[]')
                # Load the Excel file
                file_path = os.path.join(temporary_path, filename)
                xls = pd.ExcelFile(file_path)
                # Check if 'VPCs' sheet is in the file
                if 'VPCs' in xls.sheet_names:
                    print(f"Processing file: {filename}")
                    # Read 'VPCs' sheet
                    df = pd.read_excel(xls, sheet_name='VPCs')
                    # Filter columns if required columns are present
                    if {'AWS ID', 'VPC Name', 'VPC ID', 'VPC CIDR', 'Total IPs', 'Available IPs'}.issubset(df.columns):
                        df_filtered = df[['AWS ID', 'VPC Name', 'VPC ID', 'VPC CIDR', 'Total IPs', 'Available IPs']].copy()
                        df_filtered.insert(0, 'Account Name', account_name)
                        # Ensure AWS ID is treated as text
                        df_filtered['AWS ID'] = df_filtered['AWS ID'].astype(str)
                        data_list.append(df_filtered)
                    else:
                        print(f"Required columns not found in file: {filename}")
                else:
                    print(f"Sheet 'VPCs' not found in file: {filename}")
            except Exception as e:
                print(f"Warning: Skipping file {filename} due to error: {e}")

    # Concatenate all data and save to Excel
    if data_list:
        final_df = pd.concat(data_list, ignore_index=True)
        current_date = datetime.now().strftime('%y_%m_%d')
        file_name = f"CloudOps_Netrix_{current_date}.xlsx"
        file_name_with_dir = os.path.join(temporary_path, file_name)
        final_df.to_excel(file_name_with_dir, index=False, sheet_name='IP Ranges')
        workbook_with_format(file_name_with_dir)
        print(f"Data successfully saved to {file_name_with_dir}.")
    else:
        print("No data to save.")

if __name__ == "__main__":
    # Get AWS profile names
    profile_names = get_aws_profiles("~/.aws/config")
    if profile_names:
        multi_inventory_maker(profile_names)
    else:
        single_inventory_maker("default")
    netrix_maker()
