import json
import os
import uuid
from datetime import datetime, timezone

import boto3

s3 = boto3.client("s3")

ANALYTICS_BUCKET = os.environ["ANALYTICS_BUCKET"]
SOURCE_PREFIX = os.environ["SOURCE_PREFIX"]


def handler(event, context):
    """Registra un evento de auditoria (job, tabla, filas, estado) de la
    fuente sqlserver como un objeto JSON en el bucket analytics.
    """
    record = {
        "source": SOURCE_PREFIX,
        "job_name": event.get("job_name"),
        "table": event.get("table"),
        "status": event.get("status", "unknown"),
        "row_count": event.get("row_count"),
        "audited_at": datetime.now(timezone.utc).isoformat(),
    }

    key = f"audit/{SOURCE_PREFIX}/{record['audited_at']}-{uuid.uuid4().hex}.json"
    s3.put_object(
        Bucket=ANALYTICS_BUCKET,
        Key=key,
        Body=json.dumps(record).encode("utf-8"),
        ContentType="application/json",
    )

    return {"statusCode": 200, "audit_key": key}
