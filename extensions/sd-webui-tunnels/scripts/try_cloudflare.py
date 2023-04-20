# credit to camenduru senpai
from pycloudflared import try_cloudflare

from modules.shared import cmd_opts

from gradio import strings

import os

if cmd_opts.cloudflared:
    print("cloudflared detected, trying to connect...")
    port = cmd_opts.port if cmd_opts.port else 7860
    tunnel_url = try_cloudflare(port=port, verbose=False)
    os.environ['webui_url'] = tunnel_url.tunnel
    strings.en["PUBLIC_SHARE_TRUE"] = f"Running on public URL: {tunnel_url.tunnel}"
