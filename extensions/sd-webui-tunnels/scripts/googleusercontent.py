import os

from discord_webhook import send_to_discord
from modules.shared import cmd_opts
from gradio import strings
import os

is_colab = "COLAB_RELEASE_TAG" in os.environ or "COLAB_BACKEND_VERSION" in os.environ

if is_colab and cmd_opts.googleusercontent:
    print("googleusercontent detected, trying to connect...")

    if not getattr(cmd_opts, "no_gradio_queue", True):
        msg = " * If without `--no-gradio-queue` option, it will not work on google colab."
        print(msg)

    from google.colab.output import eval_js

    port = cmd_opts.port if cmd_opts.port else 7860
    js = "google.colab.kernel.proxyPort(" + str(port) + ", {'cache': false})"
    tunnel_url = eval_js(js)
    print(f" * Running on {tunnel_url}")
    os.environ['webui_url'] = tunnel_url
    colab_url = os.getenv('colab_url')
    strings.en["SHARE_LINK_MESSAGE"] = f"Running on public URL (recommended): {tunnel_url}"

    if cmd_opts.tunnel_webhook:
        send_to_discord(tunnel_url, cmd_opts.tunnel_webhook)
