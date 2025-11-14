import json, os, time, uuid, boto3
from boto3.dynamodb.conditions import Key

TABLE_NAME = os.environ["TABLE_NAME"]
ddb = boto3.client("dynamodb")

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
    method = event.get("httpMethod")

    # Check for authentication
    uid = get_user_id(event)
    if not uid:
        return {"statusCode": 401, "headers": CORS, "body": json.dumps({"error": "Unauthorized user"})}

    if method == "OPTIONS":
        return {"statusCode": 204, "headers": CORS, "body": ""}

    if method == "POST":
        return create_order(event, uid)

    if method == "GET":
        path_params = event.get("pathParameters") or {}
        order_id = path_params.get("id")
        if order_id:
            return get_order(order_id, uid)
        return list_orders(uid)

    return {"statusCode": 405, "headers": CORS, "body": json.dumps({"error": "Method Not Allowed"})}


def create_order(event, uid):
    try:
        payload = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
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
    except Exception as e:
        print("DynamoDB error:", e)
        return {"statusCode": 500, "headers": CORS, "body": json.dumps({"error": "Failed to persist order"})}

    return {"statusCode": 200, "headers": CORS, "body": json.dumps({"ok": True, "orderId": order_id})}


def list_orders(uid):
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
    try:
        resp = ddb.get_item(
            TableName=TABLE_NAME,
            Key={"orderId": {"S": order_id}},
            ConsistentRead=True,
        )
        item = resp.get("Item")
        if not item:
            return {"statusCode": 404, "headers": CORS, "body": json.dumps({"error": "Order not found"})}
        
        if item.get("userId", {}).get("S") != uid:
            return {"statusCode": 403, "headers": CORS, "body": json.dumps({"error": "Not authorized to view this order"})}
        
        return {"statusCode": 200, "headers": CORS, "body": json.dumps({"order": item}, default=str)}
    except Exception as e:
        print("GetItem error:", e)
        return {"statusCode": 500, "headers": CORS, "body": json.dumps({"error": "Failed to fetch order"})}
