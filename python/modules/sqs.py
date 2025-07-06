from modules.common import exponential_backoff

def list_sqs_queues(session):
    client = session.client('sqs')
    queue_urls = exponential_backoff(client.list_queues).get("QueueUrls", [])

    result = []

    for queue_url in queue_urls:
        attrs = exponential_backoff(client.get_queue_attributes, QueueUrl=queue_url, AttributeNames=['All']).get("Attributes", {})

        result.append({
            "Queue Name": queue_url.split("/")[-1],
            "Queue URL": queue_url,
            "Visibility Timeout": attrs.get("VisibilityTimeout", "-"),
            "Message Retention Period": attrs.get("MessageRetentionPeriod", "-"),
            "Maximum Message Size": attrs.get("MaximumMessageSize", "-"),
            "Created Timestamp": attrs.get("CreatedTimestamp", "-"),
            "Last Modified Timestamp": attrs.get("LastModifiedTimestamp", "-"),
            "Approximate Number Of Messages": attrs.get("ApproximateNumberOfMessages", "-"),
            "Encryption": attrs.get("KmsMasterKeyId", "-")
        })

    return result
