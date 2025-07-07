from modules.common import exponential_backoff
import re
import pandas as pd

def fetch_all_sg_data(session):
    ec2 = session.client('ec2')
    region = session.region_name

    sg_data = exponential_backoff(ec2.describe_security_groups)
    eni_data = exponential_backoff(ec2.describe_network_interfaces)
    ec2_data = exponential_backoff(ec2.describe_instances)

    ec2_name_map = build_ec2_name_map(ec2_data)

    sg_summary = pd.DataFrame(map_sg_summary(region, sg_data, eni_data, ec2_name_map))
    sg_rules = pd.DataFrame(map_sg_rules_with_resources(region, sg_data, eni_data, ec2_name_map))
    sg_findings = findings_rules_with_governance(sg_rules)

    return (
        sg_summary,
        sg_rules,
        sg_findings
    )

def build_ec2_name_map(ec2_data):
    return {
        inst.get("InstanceId"): next((tag.get("Value") for tag in inst.get("Tags", []) if tag.get("Key") == "Name"), "-")
        for res in ec2_data.get("Reservations", [])
        for inst in res.get("Instances", [])
    }

def infer_resource_type(description, interface_type):
    desc = (description or '').lower()
    if 'lambda' in desc: return 'Lambda'
    if 'elb' in desc: return 'ELB'
    if 'rds' in desc: return 'RDS'
    if 'msk' in desc or 'kafka' in desc: return 'MSK'
    if 'opensearch' in desc or 'es endpoint' in desc: return 'OpenSearch'
    if 'efs' in desc or 'mount target' in desc: return 'EFS'
    if 'nat gateway' in desc: return 'NAT Gateway'
    if 'transit gateway' in desc or 'tgw' in desc: return 'Transit Gateway'
    if 'vpce' in desc or 'vpc endpoint' in desc: return 'VPC Endpoint'
    if 'redshift' in desc: return 'Redshift'
    if 'global accelerator' in desc: return 'Global Accelerator'
    if interface_type == 'interface': return 'EC2'
    return 'Unknown'

def map_sg_summary(region, sg_data, eni_data, ec2_name_map):
    sg_list = sg_data['SecurityGroups']

    sg_to_resources = {}
    for eni in eni_data['NetworkInterfaces']:
        eni_id = eni.get('NetworkInterfaceId', '-')
        private_ip = eni.get('PrivateIpAddress', '-')
        description = eni.get('Description', '-')
        interface_type = eni.get('InterfaceType', '-')
        resource_id = eni.get('Attachment', {}).get('InstanceId') or description or '-'
        resource_type = infer_resource_type(description, interface_type)
        resource_name = ec2_name_map.get(resource_id, '-') if resource_type == 'EC2' else '-'

        sg_info = {
            'Resource ID': resource_id,
            'Resource Type': resource_type,
            'Resource Name': resource_name,
            'ENI ID': eni_id,
            'Private IP': private_ip
        }

        for group in eni.get('Groups', []):
            sg_id = group['GroupId']
            sg_to_resources.setdefault(sg_id, []).append(sg_info)

    result = []
    for sg in sg_list:
        sg_id = sg['GroupId']
        sg_name = next((tag['Value'] for tag in sg.get('Tags', []) if tag['Key'] == 'Name'), sg.get('GroupName', '-'))
        description = sg.get('Description', '-')
        usage = sg_id in sg_to_resources
        resources = sg_to_resources.get(sg_id, [{
            'Resource ID': '-', 'Resource Type': '-', 'Resource Name': '-', 'ENI ID': '-', 'Private IP': '-'
        }])

        for res in resources:
            result.append({
                'Security Group Name': sg_name,
                'Security Group ID': sg_id,
                'SG Description': description,
                'Region': region,
                'Usage': usage,
                'Resource Name': res['Resource Name'],
                'Resource ID': res['Resource ID'],
                'Resource Type': res['Resource Type'],
                'ENI ID': res['ENI ID'],
                'Private IP': res['Private IP']
            })

    return result

def map_sg_rules_with_resources(region, sg_data, eni_data, ec2_name_map):
    sg_list = sg_data['SecurityGroups']

    sg_name_map = {
        sg['GroupId']: next((tag['Value'] for tag in sg.get('Tags', []) if tag['Key'] == 'Name'), sg.get('GroupName', '-'))
        for sg in sg_list
    }

    eni_map = {}
    for eni in eni_data['NetworkInterfaces']:
        eni_id = eni.get('NetworkInterfaceId', '-')
        private_ip = eni.get('PrivateIpAddress', '-')
        description = eni.get('Description', '-')
        interface_type = eni.get('InterfaceType', '-')
        resource_id = eni.get('Attachment', {}).get('InstanceId') or description or '-'
        resource_type = infer_resource_type(description, interface_type)
        resource_name = ec2_name_map.get(resource_id, '-') if resource_type == 'EC2' else '-'

        for group in eni.get('Groups', []):
            sg_id = group['GroupId']
            eni_map.setdefault(sg_id, []).append({
                'ENI ID': eni_id,
                'Private IP': private_ip,
                'Resource ID': resource_id,
                'Resource Type': resource_type,
                'Resource Name': resource_name
            })

    result = []

    for sg in sg_list:
        sg_id = sg['GroupId']
        sg_name = sg_name_map.get(sg_id, '-')
        description = sg.get('Description', '-')
        usage_flag = sg_id in eni_map
        attached_resources = eni_map.get(sg_id, [{
            'ENI ID': '-', 'Private IP': '-', 'Resource ID': '-', 'Resource Type': '-', 'Resource Name': '-'
        }])

        def build_rule_rows(rules, direction):
            rows = []
            for rule in rules:
                protocol = rule.get('IpProtocol', '-')
                protocol = 'all' if protocol == '-1' else protocol
                from_port = rule.get('FromPort', '-')
                to_port = rule.get('ToPort', '-')
                port_range = f"{from_port}-{to_port}" if from_port != to_port else f"{from_port}"

                sources = []
                sources.extend([(ip.get('CidrIp', '-'), ip.get('Description', '-')) for ip in rule.get('IpRanges', [])])
                sources.extend([(ip.get('CidrIpv6', '-'), ip.get('Description', '-')) for ip in rule.get('Ipv6Ranges', [])])
                sources.extend([(group.get('GroupId', '-'), group.get('Description', '-')) for group in rule.get('UserIdGroupPairs', [])])

                for origin, origin_desc in sources:
                    parsed_name = sg_name_map.get(origin, origin)
                    for res in attached_resources:
                        rows.append({
                            'Security Group Name': sg_name,
                            'Security Group ID': sg_id,
                            'SG Description': description,
                            'Region': region,
                            'Usage': usage_flag,
                            'Direction': direction,
                            'Protocol': protocol,
                            'Port Range': port_range,
                            'Src Origin': origin if direction == 'Inbound' else '-',
                            'Src Parsed': parsed_name if direction == 'Inbound' else '-',
                            'Des Origin': origin if direction == 'Outbound' else '-',
                            'Des Parsed': parsed_name if direction == 'Outbound' else '-',
                            'Rules Src/Dst Description': origin_desc,
                            'Resource Name': res['Resource Name'],
                            'Resource ID': res['Resource ID'],
                            'Resource Type': res['Resource Type'],
                            'ENI ID': res['ENI ID'],
                            'Private IP': res['Private IP']
                        })
            return rows

        result.extend(build_rule_rows(sg.get('IpPermissions', []), 'Inbound'))
        result.extend(build_rule_rows(sg.get('IpPermissionsEgress', []), 'Outbound'))

    return result

def findings_rules_with_governance(sg_data):
    try:
        df = pd.DataFrame(sg_data)

        def analyze_sg(row):
            findings = []
            direction = row.get("Direction", "")
            port = str(row.get("Port Range", ""))
            source = str(row.get("Src Origin", ""))
            source_name = str(row.get("Src Parsed", ""))
            destination = str(row.get("Des Origin", ""))
            destination_name = str(row.get("Des Parsed", ""))
            protocol = str(row.get("Protocol", "")).lower()
            sg_id = row.get("Security Group ID", "")

            is_sg_source = source.startswith("sg-")
            is_sg_dest = destination.startswith("sg-")

            
            # Rule 1: overly open to 0.0.0.0/0
            if direction == "Inbound" and source == "0.0.0.0/0" and (
                re.search(r"^22$|^22[-:]", port) or protocol == "all"
            ):
                findings.append("Inbound 0.0.0.0/0 open (22/ALL)")

            if direction == "Outbound" and destination == "0.0.0.0/0" and protocol == "all":
                findings.append("Outbound 0.0.0.0/0 open (ALL)")

            # Rule 2: unused SG
            if str(row.get("Usage", "")).strip().upper() == "FALSE":
                findings.append("Unused SG")

            # Rule 3: SG reference mismatch
            # --- Outbound: referencing a destination SG ---
            if direction == "Outbound" and is_sg_dest:
                matched_inbound = (
                    (df["Security Group ID"] == destination) &
                    (df["Direction"] == "Inbound") &
                    (df["Src Origin"] == sg_id)
                )
                if not matched_inbound.any():
                    # Check if target SG is just open to 0.0.0.0/0
                    open_inbound = (
                        (df["Security Group ID"] == destination) &
                        (df["Direction"] == "Inbound") &
                        (df["Src Origin"] == "0.0.0.0/0")
                    )
                    if open_inbound.any():
                        findings.append(f"Outbound references {destination_name} but no matching inbound (note: {destination_name} open to 0.0.0.0/0)")
                    else:
                        findings.append(f"Outbound references {destination_name} but no matching inbound")

            # --- Inbound: referencing a source SG ---
            if direction == "Inbound" and is_sg_source:
                matched_outbound = (
                    (df["Security Group ID"] == source) &
                    (df["Direction"] == "Outbound") &
                    (df["Des Origin"] == sg_id)
                )
                if not matched_outbound.any():
                    # Check if source SG is open to 0.0.0.0/0
                    open_outbound = (
                        (df["Security Group ID"] == source) &
                        (df["Direction"] == "Outbound") &
                        (df["Des Origin"] == "0.0.0.0/0")
                    )
                    if open_outbound.any():
                        findings.append(f"Inbound references {source_name} but no matching outbound (note: {source_name} open to 0.0.0.0/0)")
                    else:
                        findings.append(f"Inbound references {source_name} but no matching outbound")

            return ", ".join(findings)


        df["Findings"] = df.apply(analyze_sg, axis=1)
        df_filtered = df[df["Findings"] != ""]
        columns_to_drop = [
            "Usage", "Region", "Src Origin", "Des Origin", 
            "Resource Name", "Resource ID", "Resource Type", 
            "ENI ID", "Private IP", "Security Group ID", "SG Description"
        ]
        df_filtered = df_filtered.drop(columns=[col for col in columns_to_drop if col in df_filtered.columns])
        df_filtered = df_filtered.drop_duplicates()
        cols = df_filtered.columns.tolist()
        if "Findings" in cols:
            cols.insert(0, cols.pop(cols.index("Findings")))
            df_filtered = df_filtered[cols]

        return df_filtered

    except Exception as e:
        return str(e), 500