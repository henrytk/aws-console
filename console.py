import sys

from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.shortcuts import print_container
from prompt_toolkit.widgets import Frame, TextArea
from prompt_toolkit.shortcuts import set_title, clear_title
import boto3


class EC2InstancesDescriber():
    def run(args):
        client = boto3.client("ec2")
        print(client.describe_instances())


CONSOLE_MAP = {
    # Structure:
    # AWS -> Services -> Resources -> Actions
    "aws": {
        "ec2": {
            "instances": {
                "describe": ec2_instances_list
            }
        }
    }
}


class Path():
    def __init__(self, path):
        self.path = path
        self.choices = self.build_choices()
        self.prompt = self.build_prompt()
        self.placeholder = self.build_placeholder()
        self.completer = self.build_completer()
        self.aws_api_function = None


    def build_choices(self):
        console_map = CONSOLE_MAP.copy()
        for p in self.path:
            try:
                console_map = console_map[p]
            except KeyError as key_error:
                print("Error: malformed path looked up in console map")
                print(key_error)
                sys.exit(1)
        return console_map.keys()


    def build_prompt(self):
        prompt = "".join([path_bit + " > " for path_bit in self.path])
        return FormattedText([("fg:Orange", prompt)])


    def build_placeholder(self):
        return FormattedText([("fg:DimGrey", " | ".join(self.choices))])


    def build_completer(self):
        return WordCompleter(self.choices, ignore_case=True)


    def selection_is_valid(self, selection):
        if selection not in self.choices:
            return False
        return True


class ConsoleRunner():
    def __init__(self):
        self.initial_path = ["aws"]
        set_title("AWS Console")
        ConsoleRunner.print_context()

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
        run_prompt(Path(self.initial_path))

    def exit(self):
        clear_title()
        print("GoodBye!")

def run_prompt(path):
    session = PromptSession(
        history=InMemoryHistory(),
        auto_suggest=AutoSuggestFromHistory(),
        enable_history_search=True,
        completer=path.completer,
    )
    while True:
        try:
            selection = session.prompt(path.prompt, placeholder=path.placeholder)
            if not path.selection_is_valid(selection):
                raise SelectionError(path, selection)
            child_path = path.path.copy()
            child_path.append(selection.lower())
            run_prompt(Path(child_path))
        except SelectionError as selection_error:
            print_formatted_text(FormattedText([("fg:Red", str(selection_error))]))
            continue
        except KeyboardInterrupt:
            continue  # Control-C pressed. Try again.
        except EOFError:
            break  # Control-D pressed.


class SelectionError(Exception):
    def __init__(self, path, selection):
        self.message = "Invalid selection: {}\nChoices: {}".format(selection, ", ".join(path.choices))
        super().__init__(self.message)


if __name__ == '__main__':
    console_runner = ConsoleRunner()
    console_runner.run()
    console_runner.exit()
