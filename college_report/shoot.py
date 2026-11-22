"""Screenshots of the local Streamlit dashboard through Chrome's DevTools protocol: open a page, optionally click a tab, wait, capture."""
import base64, json, subprocess, sys, time, urllib.request
import websocket

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
proc = subprocess.Popen([CHROME, "--headless=new", "--remote-debugging-port=9333", "--window-size=1440,1000", "--hide-scrollbars",
                         "--user-data-dir=/tmp/apexiq-shot-profile", "about:blank"], stderr=subprocess.DEVNULL)
for _ in range(50):
    try:
        tab = json.load(urllib.request.urlopen("http://127.0.0.1:9333/json"))[0]; break
    except Exception:
        time.sleep(0.2)
ws = websocket.create_connection(tab["webSocketDebuggerUrl"], timeout=120)
n = 0
def cdp(method, **params):
    global n; n += 1
    ws.send(json.dumps({"id": n, "method": method, "params": params}))
    while True:
        m = json.loads(ws.recv())
        if m.get("id") == n:
            return m.get("result", {})
def js(expr):
    return cdp("Runtime.evaluate", expression=expr, awaitPromise=True, returnByValue=True).get("result", {}).get("value")

cdp("Emulation.setDeviceMetricsOverride", width=1440, height=2600, deviceScaleFactor=1.5, mobile=False)
out_dir = sys.argv[1]
for spec in json.load(open(sys.argv[2])):  # [{"name", "url", "tab"?, "height"?, "scroll"?}]
    cdp("Page.navigate", url=spec["url"]); time.sleep(spec.get("wait", 9))
    if spec.get("tab"):
        js(f"""[...document.querySelectorAll('[role=tab]')].find(b => b.innerText.trim() === {json.dumps(spec['tab'])})?.click()""")
        time.sleep(spec.get("tab_wait", 6))
    js("document.querySelector('[data-testid=stSidebar]')?.remove(); document.querySelector('header')?.remove();")
    top = js(f"""(() => {{ const m = document.querySelector('section.main, [data-testid=stMain]'); m.scrollTop = {spec.get('scroll', 0)}; return 0; }})()""")
    time.sleep(1.5)
    shot = cdp("Page.captureScreenshot", format="png", clip={"x": 140, "y": spec.get("y", 90), "width": 1160, "height": spec.get("height", 1000), "scale": 1})
    open(f"{out_dir}/{spec['name']}.png", "wb").write(base64.b64decode(shot["data"]))
    print("saved", spec["name"])
proc.terminate()
