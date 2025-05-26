import pandas as pd
from modules.common import exponential_backoff

def sanitize_sheet_name(zone_name):
    name = zone_name.replace('.', '_')
    return name[:28] + "..." if len(name) > 31 else name

def list_route53_zones(session):
    client = session.client('route53')
    zones = exponential_backoff(client.list_hosted_zones)['HostedZones']
    zone_summary = []
    for z in zones:
        zone_summary.append({
            "Hosted zone name": z['Name'],
            "Type": "Private" if z['Config']['PrivateZone'] else "Public",
            "Record count": z.get('ResourceRecordSetCount', '-'),
            "Description": z['Config'].get('Comment', '-')
        })
    return zones, pd.DataFrame(zone_summary)

def list_zone_record_sets(session, zone_id):
    client = session.client('route53')
    paginator = client.get_paginator('list_resource_record_sets')
    records = []
    for page in paginator.paginate(HostedZoneId=zone_id):
        for record in page['ResourceRecordSets']:
            alias = 'AliasTarget' in record
            value = "-"
            if 'ResourceRecords' in record:
                value = ", ".join(r['Value'] for r in record['ResourceRecords'])
            elif alias:
                value = record['AliasTarget']['DNSName']
            records.append({
                "Record name": record['Name'],
                "Type": record['Type'],
                "Routing policy": "Simple",
                "Differentiator": "-",
                "Alias": "Yes" if alias else "No",
                "Value / Route traffic to": value,
                "TTL (seconds)": record.get('TTL', '-'),
                "Health check ID": record.get('HealthCheckId', '-'),
                "Evaluate target health": record.get('AliasTarget', {}).get('EvaluateTargetHealth', '-') if alias else '-'
            })
    return pd.DataFrame(records)
