import sys

from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.shortcuts import print_container
from prompt_toolkit.widgets import Frame, TextArea
from prompt_toolkit.shortcuts import set_title, clear_title
import boto3

class AWSConsole():
    def __init__(self):
        set_title("AWS Console")
        AWSConsole.print_context()
        self.prompt_stack = []

    @staticmethod
    def print_context():
        sts = boto3.client("sts")
        try:
            caller_identity = sts.get_caller_identity()
        except Exception as e:
            print("Error while getting caller identity: {}".format(e))
            sys.exit(1)
        print_container(
            Frame(
                TextArea(text="User ID: {}\nAccount: {}\nCaller ARN: {}".format(
                    caller_identity["UserId"],
                    caller_identity["Account"],
                    caller_identity["Arn"],
                )),
                title="AWS Console",
            )
        )

    def run(self):
        self.prompt_stack.append(AWSPrompt())
        self.prompt_stack[0].run()

    def exit(self):
        clear_title()
        print("GoodBye!")

class AWSPrompt():
    def __init__(self):
        self.completer = WordCompleter(
            [
                "EC2",
                "S3",
            ],
            ignore_case=True,
        )
        self.prompt = FormattedText([("fg:Orange", "AWS > ")])
        self.placeholder = FormattedText([("fg:DimGrey", "Enter AWS service, for example: ec2")])


        self.session = PromptSession(
            history=InMemoryHistory(),
            auto_suggest=AutoSuggestFromHistory(),
            enable_history_search=True,
            completer=self.completer,
        )

    def run(self):
        while True:
            try:
                text = self.session.prompt(self.prompt, placeholder=self.placeholder)
            except KeyboardInterrupt:
                continue  # Control-C pressed. Try again.
            except EOFError:
                break  # Control-D pressed.

def main():
    aws_console = AWSConsole()
    aws_console.run()
    aws_console.exit()

if __name__ == '__main__':
    main()
