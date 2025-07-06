from modules.common import exponential_backoff

def list_lambda_functions(session):
    client = session.client('lambda')
    paginator = client.get_paginator('list_functions')

    result = []

    for page in paginator.paginate():
        for function in page.get("Functions", []):
            result.append({
                "Function Name": function.get("FunctionName", "-"),
                "Runtime": function.get("Runtime", "-"),
                "Handler": function.get("Handler", "-"),
                "Role": function.get("Role", "-"),
                "Memory Size": function.get("MemorySize", "-"),
                "Timeout": function.get("Timeout", "-"),
                "Last Modified": function.get("LastModified", "-"),
                "Version": function.get("Version", "-"),
                "State": function.get("State", "-"),
                "Package Type": function.get("PackageType", "-"),
                "ARN": function.get("FunctionArn", "-")
            })

    return result
