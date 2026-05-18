# theres no exploit here, its just so that it doesnt clutter the crypto :3

import time
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.live import Live
from rich.text import Text
from random import random

console = Console(force_terminal=True)

def _typing(sender, message):
    if not console.is_terminal:
        return
    duration = min(0.6 + len(str(message)) * 0.025, 2.5)
    with Live(
        Text(f"  {sender} is typing...", style="dim italic cyan"),
        console=console,
        transient=True,
        refresh_per_second=12,
    ):
        time.sleep(duration)


def _read_receipt():
    if not console.is_terminal:
        return
    time.sleep(random()*5)
    now = datetime.now().strftime("%H:%M")
    console.print(Align.right(Text(f"Read {now}", style="dim")))


def print(sender=None, message=None):
    if message is None:
        import builtins
        builtins.print(sender)
        return
    if sender!="You":
        _typing(sender, message)
        panel = Panel(
            f"[bold white]{message}[/bold white]",
            title=f"{sender}",
            border_style="cyan",
            expand=False,
        )
        console.print(panel)
    else:
        panel = Panel(
            f"[white]{message}[/white]",
            title="You",
            border_style="green",
            expand=False,
        )
        console.print(Align.right(panel))
        _read_receipt()


def input():
    result = console.input("[bold green]Type message > [/bold green]")
    if console.is_terminal:
        console.file.write("\033[1A\033[2K\r")
        console.file.flush()
    return result
