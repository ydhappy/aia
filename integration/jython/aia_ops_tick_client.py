# Jython 2.7 compatible AIA ops-tick client.
# This file intentionally avoids Python 3-only syntax so legacy Java servers can embed it.

from java.io import BufferedReader, InputStreamReader, OutputStreamWriter
from java.net import URL


class AiaOpsTickClient(object):
    def __init__(self, base_url, api_key=""):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or ""

    def post_json(self, path, json_body, connect_timeout_ms=1200, read_timeout_ms=3500):
        url = URL(self.base_url + path)
        conn = url.openConnection()
        conn.setRequestMethod("POST")
        conn.setConnectTimeout(connect_timeout_ms)
        conn.setReadTimeout(read_timeout_ms)
        conn.setRequestProperty("Accept", "application/json")
        conn.setRequestProperty("Content-Type", "application/json; charset=UTF-8")
        if self.api_key:
            conn.setRequestProperty("X-API-Key", self.api_key)
        conn.setDoOutput(True)

        writer = OutputStreamWriter(conn.getOutputStream(), "UTF-8")
        try:
            writer.write(json_body)
            writer.flush()
        finally:
            writer.close()

        code = conn.getResponseCode()
        stream = conn.getErrorStream() if code >= 400 else conn.getInputStream()
        body = self._read_all(stream)
        conn.disconnect()
        if code < 200 or code >= 300:
            raise RuntimeError("AIA ops-tick failed: %s %s" % (code, body))
        return body

    def ops_tick(self, json_body):
        return self.post_json("/api/v1/robot/ops-tick", json_body)

    def decide(self, json_body):
        return self.post_json("/decide", json_body)

    def _read_all(self, stream):
        if stream is None:
            return ""
        reader = BufferedReader(InputStreamReader(stream, "UTF-8"))
        try:
            parts = []
            line = reader.readLine()
            while line is not None:
                parts.append(line)
                line = reader.readLine()
            return "".join(parts)
        finally:
            reader.close()
