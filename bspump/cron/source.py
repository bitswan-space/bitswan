import os
import json
import logging
import traceback
from collections import deque
from datetime import datetime

import aiohttp.web

from ..abc.source import TriggerSource


L = logging.getLogger(__name__)


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CronSource Dashboard</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f1117; color: #e1e4e8; padding: 24px; }}
  .header {{ display: flex; align-items: center; gap: 16px; margin-bottom: 24px; flex-wrap: wrap; }}
  .header h1 {{ font-size: 1.4rem; font-weight: 600; }}
  .badge {{ display: inline-block; padding: 4px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; }}
  .badge-active {{ background: #1a7f37; color: #fff; }}
  .badge-inactive {{ background: #6e4009; color: #fff; }}
  .status-bar {{ display: flex; gap: 24px; flex-wrap: wrap; background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; margin-bottom: 24px; font-size: 0.9rem; }}
  .status-item {{ display: flex; flex-direction: column; gap: 4px; }}
  .status-label {{ color: #8b949e; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; }}
  .trigger-section {{ margin-bottom: 24px; }}
  .btn {{ background: #238636; color: #fff; border: none; padding: 10px 20px; border-radius: 6px; font-size: 0.9rem; cursor: pointer; font-weight: 600; }}
  .btn:hover {{ background: #2ea043; }}
  .btn:disabled {{ background: #21262d; color: #484f58; cursor: not-allowed; }}
  .btn-feedback {{ margin-left: 12px; font-size: 0.85rem; }}
  table {{ width: 100%; border-collapse: collapse; background: #161b22; border: 1px solid #30363d; border-radius: 8px; overflow: hidden; }}
  th {{ text-align: left; padding: 10px 14px; background: #1c2129; color: #8b949e; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid #30363d; }}
  td {{ padding: 10px 14px; border-bottom: 1px solid #21262d; font-size: 0.85rem; }}
  tr:last-child td {{ border-bottom: none; }}
  .status-success {{ color: #3fb950; }}
  .status-error {{ color: #f85149; }}
  .status-running {{ color: #d29922; }}
  .type-cron {{ color: #8b949e; }}
  .type-manual {{ color: #58a6ff; }}
  .empty-state {{ text-align: center; padding: 32px; color: #484f58; }}
</style>
</head>
<body>
  <div class="header">
    <h1>{source_id}</h1>
    <span class="badge {auto_badge_class}">{auto_badge_text}</span>
  </div>
  <div class="status-bar">
    <div class="status-item"><span class="status-label">Stage</span><span>{stage}</span></div>
    <div class="status-item"><span class="status-label">Cron</span><span>{cron_string}</span></div>
    <div class="status-item"><span class="status-label">Next Fire</span><span id="next-fire">{next_trigger_time}</span></div>
  </div>
  <div class="trigger-section">
    <button class="btn" id="trigger-btn" onclick="doTrigger()">Trigger Now</button>
    <span class="btn-feedback" id="trigger-feedback"></span>
  </div>
  <h2 style="font-size:1.1rem; margin-bottom:12px;">Run History</h2>
  <table>
    <thead><tr><th>ID</th><th>Started</th><th>Ended</th><th>Type</th><th>Status</th></tr></thead>
    <tbody id="runs-body"><tr><td colspan="5" class="empty-state">No runs yet</td></tr></tbody>
  </table>
<script>
function doTrigger() {{
  var btn = document.getElementById('trigger-btn');
  var fb = document.getElementById('trigger-feedback');
  btn.disabled = true;
  fb.textContent = 'Triggering...';
  fetch('/trigger', {{method:'POST'}}).then(function(r){{return r.json()}}).then(function(d){{
    fb.textContent = 'Triggered!';
    btn.disabled = false;
    setTimeout(function(){{fb.textContent='';}}, 3000);
    refreshRuns();
  }}).catch(function(e){{
    fb.textContent = 'Error: ' + e;
    btn.disabled = false;
  }});
}}
function refreshRuns() {{
  fetch('/runs').then(function(r){{return r.json()}}).then(function(d){{
    document.getElementById('next-fire').textContent = d.next_trigger || '-';
    var tbody = document.getElementById('runs-body');
    if (!d.runs || d.runs.length === 0) {{
      tbody.innerHTML = '<tr><td colspan="5" class="empty-state">No runs yet</td></tr>';
      return;
    }}
    var html = '';
    for (var i = 0; i < d.runs.length; i++) {{
      var r = d.runs[i];
      var sc = r.status === 'success' ? 'status-success' : r.status === 'error' ? 'status-error' : 'status-running';
      var tc = r.trigger_type === 'manual' ? 'type-manual' : 'type-cron';
      html += '<tr><td>' + r.id + '</td><td>' + r.started + '</td><td>' + (r.ended || '-') + '</td><td class="' + tc + '">' + r.trigger_type + '</td><td class="' + sc + '">' + r.status + '</td></tr>';
    }}
    tbody.innerHTML = html;
  }}).catch(function(){{}});
}}
setInterval(refreshRuns, 5000);
refreshRuns();
</script>
</body>
</html>"""


class CronSource(TriggerSource):
    """
    A simplified source for cron-triggered pipelines.

    Provides a built-in web dashboard at `/` with:
    - Manual trigger button
    - Run history log
    - Stage-aware auto-trigger (only auto-fires in configured stages)

    Usage:
        auto_pipeline(
            source=lambda app, pipeline: CronSource(
                app, pipeline,
                config={"when": "*/10 * * * *"}
            ),
            sink=lambda app, pipeline: PPrintSink(app, pipeline),
        )

    Config (pipelines.conf or inline config dict):
        when (str): Cron expression (e.g., "0 9 * * *" for daily at 9 AM)
        init_time (datetime, optional): Initial time for cron calculation (naive)
        auto_trigger_stages (str): Comma-separated stages where cron auto-fires (default: "production")

    Environment variables:
        BITSWAN_AUTOMATION_STAGE: Current stage name, set by the platform (default: "live-dev")
    """

    ConfigDefaults = {
        "auto_trigger_stages": "production",
    }

    def __init__(self, app, pipeline, id=None, config=None):
        super().__init__(app, pipeline, id=id, config=config)

        cron_string = self.Config.get("when")
        if not cron_string:
            raise ValueError(
                "CronSource requires 'when' config parameter with cron expression"
            )

        init_time = self.Config.get("init_time")
        if init_time is None:
            init_time = datetime.now()  # naive for backward compatibility

        from ..trigger import CronTrigger

        cron_trigger = CronTrigger(app, cron_string, init_time, id=f"{self.Id}_cron")
        self.on(cron_trigger)

        self._cron_trigger = cron_trigger
        self._cron_string = cron_string
        self._run_log = deque(maxlen=100)
        self._run_counter = 0
        self._manual_trigger = False

        # Stage-aware auto-trigger
        auto_stages = self.Config.get("auto_trigger_stages", "production")
        self._current_stage = os.environ.get("BITSWAN_AUTOMATION_STAGE", "live-dev")
        self._allowed_stages = [s.strip() for s in auto_stages.split(",")]
        self._auto_trigger_active = self._current_stage in self._allowed_stages

        if not self._auto_trigger_active:
            cron_trigger.pause(True)

        # Web UI
        self._setup_web_ui(app)

    def _setup_web_ui(self, app):
        from ..http.web.server import WebServerConnection

        try:
            conn = self.Pipeline.locate_connection(app, "DefaultWebServerConnection")
        except (KeyError, RuntimeError):
            try:
                port = int(
                    os.environ.get("DEFAULT_WEB_SERVER_CONNECTION_PORT") or "8080"
                )
            except ValueError:
                port = 8080
                L.warning(
                    "DEFAULT_WEB_SERVER_CONNECTION_PORT is not a valid integer. Using default 8080."
                )

            conn = WebServerConnection(
                app,
                "DefaultWebServerConnection",
                {"port": port},
            )
            app.PumpService.add_connection(conn)

        conn.aiohttp_app.router.add_get("/", self._handle_dashboard)
        conn.aiohttp_app.router.add_post("/trigger", self._handle_trigger)
        conn.aiohttp_app.router.add_get("/runs", self._handle_runs)

    async def _handle_dashboard(self, request):
        try:
            next_time = self._cron_trigger.next_trigger_time.isoformat(timespec="seconds")
        except Exception:
            next_time = "-"

        auto_badge_class = "badge-active" if self._auto_trigger_active else "badge-inactive"
        auto_badge_text = "Auto-trigger active" if self._auto_trigger_active else "Auto-trigger inactive"

        html = DASHBOARD_HTML.format(
            source_id=self.Id,
            cron_string=self._cron_string,
            stage=self._current_stage,
            auto_badge_class=auto_badge_class,
            auto_badge_text=auto_badge_text,
            next_trigger_time=next_time,
        )
        return aiohttp.web.Response(text=html, content_type="text/html")

    async def _handle_trigger(self, request):
        self._manual_trigger = True
        self.TriggerEvent.set()
        return aiohttp.web.json_response({"status": "triggered"})

    async def _handle_runs(self, request):
        try:
            next_time = self._cron_trigger.next_trigger_time.isoformat(timespec="seconds")
        except Exception:
            next_time = None

        return aiohttp.web.json_response({
            "runs": list(self._run_log),
            "next_trigger": next_time,
            "auto_trigger_active": self._auto_trigger_active,
            "stage": self._current_stage,
        })

    async def cycle(self, *args, **kwargs):
        await self.Pipeline.ready()

        self._run_counter += 1
        trigger_type = "manual" if self._manual_trigger else "cron"
        self._manual_trigger = False

        now = datetime.now()
        entry = {
            "id": self._run_counter,
            "started": now.isoformat(timespec="seconds"),
            "ended": None,
            "status": "running",
            "trigger_type": trigger_type,
            "error": None,
        }
        self._run_log.appendleft(entry)  # newest first

        try:
            event = {
                "cron_triggered": now.isoformat(),
                "trigger_id": self.Id,
                "timestamp": now.timestamp(),
                "trigger_type": trigger_type,
                "run_id": self._run_counter,
            }
            await self.Pipeline.process(event)
            entry["status"] = "success"
        except Exception:
            entry["status"] = "error"
            entry["error"] = traceback.format_exc()
            raise
        finally:
            entry["ended"] = datetime.now().isoformat(timespec="seconds")
