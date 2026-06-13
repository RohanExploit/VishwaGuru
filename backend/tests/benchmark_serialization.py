import time
import json
from fastapi import Response
from fastapi.responses import JSONResponse

data = {
    "leaderboard": [
        {
            "user_email": "abc@def.com",
            "reports_count": 10,
            "total_upvotes": 50,
            "rank": 1,
        }
        for _ in range(100)
    ]
}
json_data = json.dumps(data)


def test_jsonresponse():
    start = time.perf_counter()
    for _ in range(10000):
        # JSONResponse internally calls json.dumps
        resp = JSONResponse(content=data)
        _ = resp.body
    return time.perf_counter() - start


def test_rawresponse():
    start = time.perf_counter()
    for _ in range(10000):
        resp = Response(content=json_data, media_type="application/json")
        _ = resp.body
    return time.perf_counter() - start


if __name__ == "__main__":
    print(f"JSONResponse: {test_jsonresponse():.4f}s")
    print(f"Response with pre-serialized JSON: {test_rawresponse():.4f}s")
