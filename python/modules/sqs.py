from modules.common import exponential_backoff
from datetime import datetime

def list_sqs_queues(session):
    client = session.client('sqs')
    queue_urls = exponential_backoff(client.list_queues).get("QueueUrls", [])

    result = []

    for queue_url in queue_urls:
        attrs = exponential_backoff(
            client.get_queue_attributes,
            QueueUrl=queue_url,
            AttributeNames=['All']
        ).get("Attributes", {})

        # Unix timestamp → datetime 변환 (문자열로 변환)
        created_ts = attrs.get("CreatedTimestamp")
        last_modified_ts = attrs.get("LastModifiedTimestamp")

        created_dt = (
            datetime.utcfromtimestamp(int(created_ts)).strftime('%Y-%m-%d %H:%M:%S')
            if created_ts else "-"
        )
        last_modified_dt = (
            datetime.utcfromtimestamp(int(last_modified_ts)).strftime('%Y-%m-%d %H:%M:%S')
            if last_modified_ts else "-"
        )

        result.append({
            "Queue Name": queue_url.split("/")[-1],
            "Queue URL": queue_url,
            "Visibility Timeout": attrs.get("VisibilityTimeout", "-"),
            "Message Retention Period": attrs.get("MessageRetentionPeriod", "-"),
            "Maximum Message Size": attrs.get("MaximumMessageSize", "-"),
            "Created Timestamp": created_dt,
            "Last Modified Timestamp": last_modified_dt,
            "Approximate Number Of Messages": attrs.get("ApproximateNumberOfMessages", "-"),
            "Encryption": attrs.get("KmsMasterKeyId", "-")
        })

    return result
