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
from modules.sg_resource_mapper import map_sg_to_resources
from modules.sg_centric_rules import map_sg_rules_with_resources
from modules.sg_summary import map_sg_summary
from modules.subnet import list_subnets
from modules.tg import list_target_groups
from modules.vpc import list_vpcs
from botocore.exceptions import BotoCoreError, ClientError, ProfileNotFound, NoCredentialsError
from modules.route53 import list_route53_zones, list_zone_record_sets, sanitize_sheet_name
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

def write_dataframes_to_excel_with_sg_map(dataframes, profile_name, session):
    if not dataframes:
        print("No data available to write to Excel.")
        return

    current_date = datetime.now().strftime('%y_%m_%d')
    file_name = f"{profile_name}_inventory_{current_date}.xlsx"
    file_name_with_dir = f"{temporary_path}{file_name}"
    os.makedirs(os.path.dirname(file_name_with_dir), exist_ok=True)

    try:
        sg_map_df = pd.DataFrame(map_sg_to_resources(session))
        sg_rules_df = pd.DataFrame(map_sg_rules_with_resources(session))
        sg_summary_df = pd.DataFrame(map_sg_summary(session))

        # Reorder: insert SG Mapping and others after Security Groups
        ordered_keys = []
        for key in dataframes.keys():
            ordered_keys.append(key)
            if key == "Security Groups":
                ordered_keys.extend(["SG-Resource No Rules", "SG-Resource Rules", "Resource-SG-Rules"])

        ordered_dataframes = {}
        for key in ordered_keys:
            if key == "Resource-SG-Rules":
                ordered_dataframes[key] = sg_map_df
            elif key == "SG-Resource Rules":
                ordered_dataframes[key] = sg_rules_df
            elif key == "SG-Resource No Rules":
                ordered_dataframes[key] = sg_summary_df
            else:
                ordered_dataframes[key] = dataframes[key]

        with pd.ExcelWriter(file_name_with_dir) as writer:
            for sheet_name, df in ordered_dataframes.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)

        workbook_with_format(file_name_with_dir)
        print(f"{profile_name} Inventory creation successful with SG sheets => {file_name}")
    except Exception as e:
        print(f"Error writing data to Excel: {e}")

def write_route53_excel(session, profile_name):
    try:
        zones, summary_df = list_route53_zones(session)
        current_date = datetime.now().strftime('%y_%m_%d')
        file_name = f"{profile_name}_route53_{current_date}.xlsx"
        file_path = os.path.join(temporary_path, file_name)
        os.makedirs(temporary_path, exist_ok=True)

        summary_df = summary_df.sort_values(by='Record count', ascending=False)

        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            summary_df.to_excel(writer, sheet_name="Hosted Zones", index=False)
            workbook = writer.book
            summary_sheet = workbook["Hosted Zones"]

            for row_idx, zone in enumerate(summary_df["Hosted zone name"], start=2):
                sheet_target = sanitize_sheet_name(zone.rstrip('.'))
                cell = summary_sheet.cell(row=row_idx, column=1)
                cell.hyperlink = f"#{sheet_target}!A1"
                cell.style = "Hyperlink"

            for z in zones:
                zone_name = z['Name'].rstrip('.')
                sheet_name = sanitize_sheet_name(zone_name)
                records_df = list_zone_record_sets(session, z['Id'])

                records_df.to_excel(writer, sheet_name=sheet_name, index=False)

                sheet = writer.sheets[sheet_name]
                row_count = records_df.shape[0] + 2  # 1(header) + data rows + 1(empty row)
                column_count = len(records_df.columns)
                end_col_letter = get_column_letter(column_count)

                sheet.merge_cells(f"A{row_count}:{end_col_letter}{row_count}")
                link_cell = sheet.cell(row=row_count, column=1)
                link_cell.value = "Go to the Route53 summary"
                link_cell.hyperlink = "#'Hosted Zones'!A1"
                link_cell.style = "Hyperlink"
                link_cell.fill = PatternFill(start_color='FFCCCC', end_color='FFCCCC', fill_type='solid')  

        workbook_with_format(file_path)
        print(f"{profile_name} Route53 created => {file_name}")
    except Exception as e:
        print(f"Error writing Route53 Excel: {e}")

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
        (list_kafka_clusters, 'MSK'),
        (list_target_groups, 'Target Groups')
    ]

    dataframes = {}
    for func, sheet_name in tqdm(resource_functions, desc=f"{profile_name} Inventory creation in progress", unit="resource"):
        try:
            data = func(session)
            if data:
                dataframes[sheet_name] = pd.DataFrame(data)
        except Exception as e:
            print(f"\nError retrieving data for {sheet_name}: {e}")

    write_dataframes_to_excel_with_sg_map(dataframes, profile_name, session)

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
        write_route53_excel(session, profile_name)
    else:
        print(f"{profile_name} Session is something wrong..")

def multi_inventory_maker(profile_names):
    print(f"### Total AWS Profiles: {len(profile_names)} ###")
    num_cores = multiprocessing.cpu_count()
    print("This module simultaneously extract AWS profile inventories using the available number of cores.")
    print(f"Currently available number of CPU cores: {num_cores}")

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

def netrix_maker():
    data_list = []
    for filename in os.listdir(temporary_path):
        if filename.endswith(".xlsx") and "_inventory_" in filename:
            try:
                account_name = filename.split('_inventory_')[0].strip('[]')
                file_path = os.path.join(temporary_path, filename)
                xls = pd.ExcelFile(file_path)
                if 'VPCs' in xls.sheet_names:
                    print(f"Processing file: {filename}")
                    df = pd.read_excel(xls, sheet_name='VPCs')
                    if {'AWS ID', 'VPC Name', 'VPC ID', 'VPC CIDR', 'Total IPs', 'Available IPs'}.issubset(df.columns):
                        df_filtered = df[['AWS ID', 'VPC Name', 'VPC ID', 'VPC CIDR', 'Total IPs', 'Available IPs']].copy()
                        df_filtered.insert(0, 'Account Name', account_name)
                        df_filtered['AWS ID'] = df_filtered['AWS ID'].astype(str)
                        data_list.append(df_filtered)
                    else:
                        print(f"Required columns not found in file: {filename}")
                else:
                    print(f"Sheet 'VPCs' not found in file: {filename}")
            except Exception as e:
                print(f"Warning: Skipping file {filename} due to error: {e}")

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
    profile_names = get_aws_profiles("~/.aws/config")
    if profile_names:
        multi_inventory_maker(profile_names)
    else:
        single_inventory_maker("default")
    netrix_maker()