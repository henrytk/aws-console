#!/usr/bin/env python

import boto3
import sys

from pygments.lexers.html import HtmlLexer

from prompt_toolkit.application import Application
from prompt_toolkit.application.current import get_app
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.layout.containers import Float, HSplit, VSplit, Window
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout.menus import CompletionsMenu
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import Style
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.widgets import (
    Box,
    Button,
    Checkbox,
    Dialog,
    Frame,
    Label,
    MenuContainer,
    MenuItem,
    ProgressBar,
    RadioList,
    TextArea,
)

def ex():
    print("blah")
    sys.exit(1)

def get_caller_identity():
    client = boto3.client("sts")
    caller_identity =  client.get_caller_identity()
    return "User ID: {}\nAccount: {}\nCaller ARN: {}".format(
        caller_identity["UserId"],
        caller_identity["Account"],
        caller_identity["Arn"],
    )


def do_exit():
    get_app().exit(result=False)

console_area = Frame(body=TextArea())
service_radio = RadioList(
    values=[
        ("ec2", "ec2"),
        ("s3", "s3"),
        ("vpc", "vpc"),
        ("route53", "route53"),
        ("ecr", "ecr"),
        ("blah", "blah"),
    ],
)
service_selection_frame = service_radio
root_container = HSplit(
    [
        Window(FormattedTextControl("AWS > "), height=1, style="reverse"),
        service_selection_frame,
        console_area,
        Frame(
            title="Caller Identity",
            body=Window(
                FormattedTextControl(
                    text=get_caller_identity(),
                    focusable=False,
                ),
                height=3,
            ),
        ),
    ]
)

root_container = MenuContainer(
    body=root_container,
    menu_items=[
        MenuItem(
            "File",
            children=[
                MenuItem("Exit", handler=do_exit),
            ],
        ),
    ],
    floats=[
        Float(
            xcursor=True,
            ycursor=True,
            content=CompletionsMenu(max_height=16, scroll_offset=1),
        ),
    ],
)

# Global key bindings.
bindings = KeyBindings()
bindings.add("tab")(focus_next)
bindings.add("s-tab")(focus_previous)
@bindings.add('c-c', eager=True)
def _(event):
    event.app.exit()


style = Style.from_dict(
    {
        "window.border": "#888888",
        "shadow": "bg:#222222",
        "menu-bar": "bg:Orange #ffffff",
        "menu-bar.selected-item": "bg:#ffffff #000000",
        "menu": "bg:Orange #ffffff",
        "menu.border": "#aaaaaa",
        "window.border shadow": "#444444",
        "focused  button": "bg:#880000 #ffffff noinherit",
        # Styling for Dialog widgets.
        "button-bar": "bg:#aaaaff",
    }
)


application = Application(
    layout=Layout(root_container, focused_element=service_selection_frame),
    key_bindings=bindings,
    style=style,
    mouse_support=True,
    full_screen=True,
)


def run():
    application.run()
    print("Goodbye")


if __name__ == "__main__":
    run()
