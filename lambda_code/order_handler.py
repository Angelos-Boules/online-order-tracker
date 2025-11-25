import json, os, time, uuid, boto3
from boto3.dynamodb.conditions import Key

TABLE_NAME = os.environ["TABLE_NAME"]
ddb = boto3.client("dynamodb")
SENDER_EMAIL = os.environ["SENDER_EMAIL"]
ses = boto3.client("ses")

CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    "Content-Type": "application/json",
}

def get_user_id(event):
    try:
        return event["requestContext"]["authorizer"]["claims"]["sub"]
    except:
        return None

def handler(event, _context):
    print("Request: ", event.get("httpMethod"), event.get("path"))

    method = event.get("httpMethod")

    # Check for authentication
    uid = get_user_id(event)
    if not uid:
        print("401: Unauthorized user")
        return {"statusCode": 401, "headers": CORS, "body": json.dumps({"error": "Unauthorized user"})}

    print(f"User: {uid}")

    if method == "OPTIONS": # 204 no content
        return {"statusCode": 204, "headers": CORS, "body": ""}

    if method == "POST":
        print("Processing POST /order")
        return create_order(event, uid)

    if method == "GET":
        print("Processing GET")
        path_params = event.get("pathParameters") or {}
        order_id = path_params.get("id")
        if order_id:
            print(f"Processing GET /order/{order_id}")
            return get_order(order_id, uid)
        
        print("Processing GET /order - all orders")
        return list_orders(uid)

    print("405: Invalid Method Request: ", method) #405
    return {"statusCode": 405, "headers": CORS, "body": json.dumps({"error": "Method Not Allowed"})}


def create_order(event, uid):
    print("Creating order")
    try:
        payload = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        print("400: Invalid POST JSON - Bad Request") 
        return {"statusCode": 400, "headers": CORS, "body": json.dumps({"error": "Invalid JSON"})}

    order_id = str(uuid.uuid4())
    ttl = int(time.time()) + 30 * 24 * 3600  # 30 days ttl so entries dont live forever in the table

    item = {
        "orderId": {"S": order_id},
        "userId": {"S": uid},
        "name": {"S": str(payload.get("name", ""))},
        "product": {"S": str(payload.get("product", ""))},
        "email": {"S": str(payload.get("email", ""))},
        "createdAt": {"S": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
        "ttl": {"N": str(ttl)},
    }

    try:
        ddb.put_item(TableName=TABLE_NAME, Item=item)
        print(f"Order {order_id} created and stored successfully")

        try:
            ses.send_email(
                Source=SENDER_EMAIL,
                Destination={"ToAddresses": [item["email"]["S"]]},
                Message={
                    "Subject": {"Data": f"Order Received: '{item['product']['S']}'"},
                    "Body": {
                        "Text": {
                            "Data": (
                                f"Hello {item['name']['S']},\n\n"
                                f"We received your order for '{item['product']['S']}'.\n"
                                f"Order ID: {order_id}\n\n"
                                "Thank you for using the Buy-N-Track!"
                            )
                        }
                    },
                },
            )
            print(f"SES: Email sent to {item['email']['S']}")
        except Exception as e:
            print("SES email error:", e)

    except Exception as e:
        print("DynamoDB error:", e)
        return {"statusCode": 500, "headers": CORS, "body": json.dumps({"error": "Failed to persist order"})}

    return {"statusCode": 200, "headers": CORS, "body": json.dumps({"ok": True, "orderId": order_id})}


def list_orders(uid):
    print(f"Getting all orders under id {uid}")
    try:
        resp = ddb.query(
            TableName=TABLE_NAME,
            IndexName="UserOrdersIndex",
            KeyConditionExpression="userId = :u",
            ExpressionAttributeValues={":u": {"S": uid}},
        )
    except Exception as e:
        print("Query error:", e)
        return {"statusCode": 500, "headers": CORS, "body": json.dumps({"error": "Failed to fetch orders"})}
    
    return {"statusCode": 200, "headers": CORS, "body": json.dumps({"orders": resp.get("Items", [])}, default=str)}


def get_order(order_id, uid):
    print(f"Getting order {order_id} for user {uid}")
    try:
        resp = ddb.get_item(
            TableName=TABLE_NAME,
            Key={"orderId": {"S": order_id}},
            ConsistentRead=True,
        )
        item = resp.get("Item")

        if not item:
            print("404: Order not found")
            return {"statusCode": 404, "headers": CORS, "body": json.dumps({"error": "Order not found"})}
        
        if item.get("userId", {}).get("S") != uid:
            print("403: Order not registered to user")
            return {"statusCode": 403, "headers": CORS, "body": json.dumps({"error": "Not authorized to view this order"})}
        
        print("Order found")
        return {"statusCode": 200, "headers": CORS, "body": json.dumps({"order": item}, default=str)}
    except Exception as e:
        print("GetItem error:", e)
        return {"statusCode": 500, "headers": CORS, "body": json.dumps({"error": "Failed to fetch order"})}
