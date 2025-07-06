from modules.common import exponential_backoff

def list_sns_topics(session):
    client = session.client('sns')
    topics = exponential_backoff(client.list_topics).get("Topics", [])

    result = []

    for topic in topics:
        topic_arn = topic.get("TopicArn", "-")
        attrs = exponential_backoff(client.get_topic_attributes, TopicArn=topic_arn).get("Attributes", {})

        result.append({
            "Topic ARN": topic_arn,
            "Display Name": attrs.get("DisplayName", "-"),
            "Owner": attrs.get("Owner", "-"),
            "Subscriptions Confirmed": attrs.get("SubscriptionsConfirmed", "-"),
            "Subscriptions Pending": attrs.get("SubscriptionsPending", "-"),
            "Subscriptions Deleted": attrs.get("SubscriptionsDeleted", "-"),
            "Effective Delivery Policy": attrs.get("EffectiveDeliveryPolicy", "-"),
            "KMS Master Key ID": attrs.get("KmsMasterKeyId", "-")
        })

    return result
