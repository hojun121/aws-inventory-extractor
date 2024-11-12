from botocore.exceptions import ClientError
from modules.common import exponential_backoff

def get_tag_value(tags, key):
    for tag in tags:
        if tag['Key'] == key:
            return tag['Value']
    return 'Unnamed'

def list_subnets(session):
    subnet_data = []
    try:
        ec2_client = session.client('ec2')
        
        subnets = exponential_backoff(ec2_client.describe_subnets)['Subnets']
        
        for subnet in subnets:
            subnet_id = subnet['SubnetId']
            cidr_block = subnet['CidrBlock']
            availability_zone = subnet['AvailabilityZone']
            vpc_id = subnet['VpcId']
            subnet_type = 'Private'
            
            # Get Subnet Name
            subnet_name = get_tag_value(subnet.get('Tags', []), 'Name')
            
            # Route Tables
            route_tables = exponential_backoff(
                ec2_client.describe_route_tables,
                Filters=[{'Name': 'association.subnet-id', 'Values': [subnet_id]}]
            ).get('RouteTables', [])
            
            route_table_ids = ', '.join([rtb['RouteTableId'] for rtb in route_tables]) if route_tables else 'None'
            route_table_names = ', '.join([get_tag_value(rtb.get('Tags', []), 'Name') for rtb in route_tables]) if route_tables else 'None'
            
            # Determine if subnet is Public based on IGW in route table
            igw_nat_tg = set()
            for route_table in route_tables:
                for route in route_table.get('Routes', []):
                    if route.get('GatewayId', '').startswith('igw-'):
                        subnet_type = 'Public'
                        igw_nat_tg.add('IGW')
                    if route.get('NatGatewayId', '').startswith('nat-'):
                        igw_nat_tg.add('NAT')
                    if route.get('TransitGatewayId', '').startswith('tgw-'):
                        igw_nat_tg.add('TG')
            
            igw_nat_tg_str = ', '.join(sorted(igw_nat_tg)) if igw_nat_tg else 'None'
            
            # Network ACLs
            network_acls = exponential_backoff(
                ec2_client.describe_network_acls,
                Filters=[{'Name': 'association.subnet-id', 'Values': [subnet_id]}]
            ).get('NetworkAcls', [])
            
            network_acl_ids = ', '.join([acl['NetworkAclId'] for acl in network_acls]) if network_acls else 'None'
            network_acl_names = ', '.join([get_tag_value(acl.get('Tags', []), 'Name') for acl in network_acls]) if network_acls else 'None'
            
            # Calculate total IPs and available IPs in the subnet
            total_ips_count = 2 ** (32 - int(cidr_block.split('/')[-1]))
            available_ips_count = subnet['AvailableIpAddressCount']
            
            # Append the gathered data to the list
            subnet_data.append({
                'Name': subnet_name,
                'ID': subnet_id,
                'Subnet Type': subnet_type,
                'Subnet CIDR Block': cidr_block,
                'Total IPs': total_ips_count,
                'Available IPs': available_ips_count,
                'Availability Zone': availability_zone,
                'Route Table ID': route_table_ids,
                'Route Table Name': route_table_names,
                'Network ACL ID': network_acl_ids,
                'Network ACL Name': network_acl_names,
                'IGW/NAT/TG': igw_nat_tg_str
            })
    except ClientError as e:
        print(f"Error retrieving Subnets: {e}")
    return subnet_data
