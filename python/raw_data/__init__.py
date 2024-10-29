import sys
import os
import re
import pandas as pd
import openpyxl
from datetime import datetime
from sqlalchemy import create_engine
from openpyxl.utils import get_column_letter
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from tqdm import tqdm


def main():
    # Input password from command
    # password=$(steampipe service start --show-password | grep 'Password:' | awk '{print $2}')
    if len(sys.argv) < 2 or sys.argv[1] == "None":
        print("No input or 'None' provided. Exiting the program.")
        sys.exit(1)

    password = sys.argv[1]
    DB_URI = f'postgresql://steampipe:{password}@127.0.0.1:9193/steampipe'
    print(DB_URI)

    try:
        engine = create_engine(DB_URI)
        connection = engine.connect()
        print("Connection successful.")
    except Exception as e:
        print("Please check your SSO or IAM permissions.")
        sys.exit(1)

    today = datetime.today().strftime('%y%m%d')
    schemas = get_schemas()
    for schema in schemas:
        output_excel_path = os.path.join('/app/inventory', f'{schema}_inventory_{today}.xlsx')
        os.makedirs('/app/inventory', exist_ok=True)
        queries = get_queries(schema)
        process_and_save_sheets(queries, output_excel_path, engine, schema)

def get_schemas():
    schemas = []
    try:
        with open(os.path.expanduser("~/.steampipe/config/aws.spc"), "r") as file:
            content = file.read()
            matches = re.findall(r'connection\s+"([^"]+)"', content)
            if matches:
                schemas.extend(matches)
    except FileNotFoundError:
        print("aws.spc File not found")
    return schemas

def get_queries(schema):
    return {
        'ec2_application_load_balancer': f'SELECT * FROM {schema}.aws_ec2_application_load_balancer',
        'ec2_autoscaling_group': f'SELECT * FROM {schema}.aws_ec2_autoscaling_group',
        'cloudfront_distribution': f'SELECT * FROM {schema}.aws_cloudfront_distribution',
        'cloudwatch_metric': f'SELECT * FROM {schema}.aws_cloudwatch_metric',
        'docdb_cluster': f'SELECT * FROM {schema}.aws_docdb_cluster',
        'docdb_cluster_instance': f'SELECT * FROM {schema}.aws_docdb_cluster_instance',
        'ebs_volume': f'SELECT * FROM {schema}.aws_ebs_volume',
        'elasticache_cluster': f'SELECT * FROM {schema}.aws_elasticache_cluster',
        'elasticache_replication_group': f'SELECT * FROM {schema}.aws_elasticache_replication_group',
        'ec2_instance': f'SELECT * FROM {schema}.aws_ec2_instance',
        'ec2_load_balancer_listener': f'SELECT * FROM {schema}.aws_ec2_load_balancer_listener',
        'ec2_network_load_balancer': f'SELECT * FROM {schema}.aws_ec2_network_load_balancer',
        'ec2_target_group': f'SELECT * FROM {schema}.aws_ec2_target_group',
        'ec2_transit_gateway': f'SELECT * FROM {schema}.aws_ec2_transit_gateway',
        'iam_group': f'SELECT * FROM {schema}.aws_iam_group',
        'iam_role': f'SELECT * FROM {schema}.aws_iam_role',
        'iam_user': f'SELECT * FROM {schema}.aws_iam_user',
        'rds_db_cluster': f'SELECT * FROM {schema}.aws_rds_db_cluster',
        'rds_db_instance': f'SELECT * FROM {schema}.aws_rds_db_instance',
        's3_bucket': f'SELECT * FROM {schema}.aws_s3_bucket',
        'vpc': f'SELECT * FROM {schema}.aws_vpc',
        'vpc_nat_gateway': f'SELECT * FROM {schema}.aws_vpc_nat_gateway',
        'vpc_network_acl': f'SELECT * FROM {schema}.aws_vpc_network_acl',
        'vpc_peering_connection': f'SELECT * FROM {schema}.aws_vpc_peering_connection',
        'vpc_route_table': f'SELECT * FROM {schema}.aws_vpc_route_table',
        'vpc_security_group': f'SELECT * FROM {schema}.aws_vpc_security_group',
        'vpc_security_group_rule': f'SELECT * FROM {schema}.aws_vpc_security_group_rule',
        'vpc_internet_gateway': f'SELECT * FROM {schema}.aws_vpc_internet_gateway',
        'vpc_subnet': f'SELECT * FROM {schema}.aws_vpc_subnet',
        'vpc_endpoint': f'SELECT * FROM {schema}.aws_vpc_endpoint',
    }


def process_and_save_sheets(queries, output_excel_path, engine, schema):
    try:
        # Execute database queries and store the results in DataFrames
        data_dict = {}
        for query in tqdm(queries, desc=f"Processing schema: {schema}"):
            data_dict[query] = pd.read_sql(queries[query], engine)

        # Use 'openpyxl' as the engine for compatibility
        with pd.ExcelWriter(output_excel_path, engine='openpyxl') as writer:
            # Iterate through each DataFrame to save to Excel
            for sheet_name, data in data_dict.items():
                if not data.empty:
                    # Check and convert datetime with timezone to string
                    for col in data.columns:
                        if pd.api.types.is_datetime64_any_dtype(data[col]):
                            if data[col].dt.tz is not None:
                                data[col] = data[col].dt.strftime('%Y-%m-%d %H:%M:%S')

                    data.to_excel(writer, sheet_name=sheet_name, index=False)

    except Exception as e:
        print(f"Error in process_and_save_sheets for schema '{schema}': {e}")


if __name__ == '__main__':
    main()


