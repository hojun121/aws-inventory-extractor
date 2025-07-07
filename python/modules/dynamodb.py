from modules.common import exponential_backoff

def list_dynamodb_tables(session):
    client = session.client('dynamodb')

    # Pagination 처리 추가
    paginator = client.get_paginator('list_tables')
    pages = paginator.paginate()

    result = []

    for page in pages:
        tables = page.get("TableNames", [])
        for table_name in tables:
            table_info = exponential_backoff(client.describe_table, TableName=table_name).get("Table", {})

            result.append({
                "Table Name": table_name,
                "Status": table_info.get("TableStatus", "-"),
                "Item Count": table_info.get("ItemCount", "-"),
                "Size (Bytes)": table_info.get("TableSizeBytes", "-"),
                "Read Capacity Units": table_info.get("ProvisionedThroughput", {}).get("ReadCapacityUnits", "-"),
                "Write Capacity Units": table_info.get("ProvisionedThroughput", {}).get("WriteCapacityUnits", "-"),
                "Creation Date": table_info.get("CreationDateTime", "-"),
                "ARN": table_info.get("TableArn", "-")
            })

    return result
