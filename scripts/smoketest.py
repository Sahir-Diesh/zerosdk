import json                      
import os                       
import secrets                  
import time

import httpx
from dotenv import load_dotenv

load_dotenv()  

host = os.environ["LANGFUSE_BASE_URL"]
auth = (os.environ["LANGFUSE_PUBLIC_KEY"], os.environ["LANGFUSE_SECRET_KEY"])

def attr(key, value):
    return {"key": key, "value": {"stringValue": value}}

trace_id = secrets.token_hex(16)   # 32 hex characters
root_span_id = secrets.token_hex(8)  # 16 hex characters
child_span_id = secrets.token_hex(8)

start = time.time_ns()
child_start = start + 5_000_000    
child_end = start + 205_000_000   
end = start + 250_000_000          

root_span = {
    "traceId": trace_id,
    "spanId": root_span_id,
    "name": "agent-run",
    "kind": 1,
    "startTimeUnixNano": str(start),
    "endTimeUnixNano": str(end),
    "attributes": [
        attr("langfuse.observation.type", "agent"),
        attr("langfuse.observation.input", json.dumps({"question": "Is this working?"})),
        attr("langfuse.observation.output", json.dumps({"answer": "Yes!"})),
    ],
    "status": {"code": 1},
}

child_span = {
    "traceId": trace_id,
    "spanId": child_span_id,
    "parentSpanId": root_span_id,
    "name": "llm-call",
    "kind": 1,
    "startTimeUnixNano": str(child_start),
    "endTimeUnixNano": str(child_end),
    "attributes": [
        attr("langfuse.observation.type", "generation"),
        attr("langfuse.observation.model.name", "gpt-4o-mini"),
        attr("langfuse.observation.input", json.dumps([{"role": "user", "content": "Is this working?"}])),
        attr("langfuse.observation.output", json.dumps({"role": "assistant", "content": "Yes!"})),
        attr("langfuse.observation.usage_details", json.dumps({"input": 12, "output": 3})),
    ],
    "status": {"code": 1},
}

payload = {
    "resourceSpans": [{
        "resource": {"attributes": [attr("service.name", "zerosdk-smoke-test")]},
        "scopeSpans": [{
            "scope": {"name": "zerosdk", "version": "0.0.1"},
            "spans": [root_span, child_span],
        }],
    }]
}

response = httpx.post(
    f"{host}/api/public/otel/v1/traces",
    json=payload,
    auth=auth,
    headers={"x-langfuse-ingestion-version": "4"},
)

print(response.status_code)
print(response.text)