from flask import Flask, request, Response
import requests

import os
TARGET_URL = os.environ.get("TARGET_URL", "https://demo-chat-play-5w7vxlobzkteqfzsjn5y2w.streamlit.app/")

app = Flask(__name__)

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def proxy(path):
    url = f"{TARGET_URL}/{path}"
    headers = {key: value for key, value in request.headers if key != 'Host'}
    resp = requests.request(
        method=request.method,
        url=url,
        headers=headers,
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False
    )
    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    response_headers = [(name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in excluded_headers]
    return Response(resp.content, resp.status_code, response_headers)
