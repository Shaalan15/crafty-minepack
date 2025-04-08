from flask import Flask, Response, request, send_file, abort
import requests
import os

app = Flask(__name__)

api_url = "https://localhost:8443/api/v2"

@app.route("/", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def root_proxy():
    # Proxy to port 8100
    try:
        proxied_response = requests.request(
            method=request.method,
            url="http://localhost:8100/",
            headers={key: value for key, value in request.headers if key != 'Host'},
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False
        )
        return Response(
            proxied_response.content,
            status=proxied_response.status_code,
            headers=dict(proxied_response.headers)
        )
    except Exception as e:
        return f"Error proxying to port 8100: {e}", 502

@app.route('/<string:server_name>/eu.pb4.polymer.autohost/main.zip')
def serve_file(server_name):
    try:
        # Try to login first
        auth_url = f"{api_url}/auth/login"
        auth_payload = {
            "username": "shaalan",
            "password": "Qfwm3772"
        }
        auth_response = requests.post(auth_url, json=auth_payload, verify=False)
        if auth_response.status_code != 200:
            abort(500, "Failed to login")

        auth_json = auth_response.json()

        token = auth_json["data"]["token"]

        headers = {
            "Authorization": f"Bearer {token}"
        }

        api_response = requests.get(f"{api_url}/servers", headers=headers, verify=False)

        if api_response.status_code != 200:
            abort(502, "Metadata API error")

        api_json = api_response.json()

        requested_server = next((server for server in api_json["data"] if str(server["server_name"]).lower() == str(server_name).lower()), None)

        if not requested_server:
            abort(404, "Server not found")

        path = requested_server["path"]

        if not path or not os.path.exists(path):
            abort(404, "File not found")

        resource_pack_path = f"{path}/polymer/resource_pack.zip"

        # Step 2: Serve the file
        return send_file(resource_pack_path, mimetype="application/zip")

    except Exception as e:
        return f"Internal error: {e}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)