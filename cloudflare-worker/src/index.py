# index.py

"""
Main entry point for python cloudflare worker
Handles HTTP requests
"""

import js
import json
import base64
from pyodide.ffi import to_js
from datetime import datetime
from queries import QUERIES
from workers import WorkerEntrypoint, Response, Request


def parse_date(date_str:str):
    if not date_str:
        return None
    date_str = date_str.strip()
    
    # sometimes date is only saved as YYYYMM
    if len(date_str) == 8:
        fmt = "%Y%m%d"
    elif len(date_str) == 6:
        fmt = "%Y%m"
    else:
        return None

    try:
        dt = datetime.strptime(date_str, fmt)
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return None

# CORS headers helper
CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type"
}

class Default(WorkerEntrypoint):
        
    async def fetch(self, request: Request) -> Response:
        # Handle CORS Preflight requests (browser checks if endpoint is compatible)
        if request.method == 'OPTIONS':
            return Response("", status=204, headers = CORS_HEADERS)

        if request.method != 'POST':
            return Response(json.dumps({"error": "Method not allowed"}), status=405, 
                            headers=CORS_HEADERS
                    )

        # process incoming json payload (if valid)
        try:
            js_payload = await request.json()
            payload = js_payload.to_py() if hasattr(js_payload, "to_py") else dict(js_payload)

            # TODO: incorporate other parameter types with dynamic query selection
            # TODO: maybe have a baseline where it creates a summary of the graph

            # test with record name
            record_name = payload.get("recordName", "")

            if not record_name:
                return Response(json.dumps({"error": "Missing record name in payload"}), status=400,
                                headers= CORS_HEADERS
                        )

            # dynamic query selection here
            query = QUERIES.get("optimal_record")

            contents = record_name.split('_')

            station = contents[1]
            date = parse_date(contents[6])

            query_parameters = {
                "station_code": station,
                'date': date,
                "target_record_name": record_name
            }
            # load env secrets
            neo_uri = self.env.NEO4J_URI

            import re
            id_match = re.search(r"://([^.]+)\.", neo_uri)
            db_name = id_match.group(1) if id_match else "neo4j"

            if neo_uri.startswith("neo4j+s://"):
                neo_uri = neo_uri.replace("neo4j+s://", "https://")
            elif neo_uri.startswith("bolt+s://"):
                neo_uri = neo_uri.replace("bolt+s://", "https://")
            elif neo_uri.startswith("bolt://"):
                neo_uri = neo_uri.replace("bolt://", "http://")

            neo_user = self.env.NEO4J_USERNAME
            neo_pass = self.env.NEO4J_PASSWORD

            creds = f"{neo_user}:{neo_pass}"
            encoded_auth = base64.b64encode(creds.encode("utf-8")).decode("utf-8")

            neo_url = f"{neo_uri.rstrip('/')}/db/{db_name}/query/v2"

            neo_body = {
                "statement": query,
                "parameters": query_parameters
            }

            fetch_options = {
                "method" : 'POST',
                "headers": {
                    "Authorization": f"Basic {encoded_auth}",
                    "Content-Type": "application/json",
                    'Accept': "application/json"
                },
                "body": json.dumps(neo_body)
            }

            res = await js.fetch(neo_url, to_js(fetch_options))

            if not res.ok:
                error_text = await res.text()
                raise Exception(f"AuraDB Error ({res.status}): {error_text}")

            res_json = await res.json()

            data = res_json.to_py() if hasattr(res_json, "to_py") else json.loads(json.dumps(res_json))

            return Response(json.dumps({'success': True, "results": data}), headers = CORS_HEADERS)
        except Exception as e:
            return Response(json.dumps({"success": False, 'error': str(e)}), status=500,
                            headers = CORS_HEADERS)

