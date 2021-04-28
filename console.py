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


def ec2_instances_describe(cmd_args):
    client = boto3.client("ec2")
    print(client.describe_instances())


class CommandNotFoundError(Exception):
    def __init__(self, cmd):
        self.message = "Invalid command: {}".format(cmd)
        super().__init__(cmd)

    def __str__(self):
        return self.message


class Console():

    navigation = {
        # Structure:
        # AWS -> Services -> Resources -> Actions
        "aws": {
            "ec2": {
                "instances": {
                    "describe": ec2_instances_describe,
                }
            }
        }
    }

    def __init__(self, position):
        self.position = position
        self.prompt = FormattedText([("fg:Orange", "aws > ")])


    def cmd(self, cmd):
        if cmd:
            try:
                cmd_args = cmd.split(" ")
                cmd_func = self.lookup_cmd_func(cmd_args)
                cmd_func(cmd_args)
            except CommandNotFoundError:
                raise


    def lookup_cmd_func(self, cmd_args):
            builtin_cmds = {
                "ls": self.ls,
                "cd": self.cd,
            }
            if cmd_args[0] in builtin_cmds:
                return builtin_cmds[cmd_args[0]]
            if cmd_args[0] in self.choices():
                if self.is_dir(cmd_args[0]):
                    return self.cd_into
                else:
                    return self.lookup_action_func(cmd_args[0])
            raise CommandNotFoundError(cmd_args[0])


    def lookup_action_func(self, action):
        navigation = self.navigation.copy()
        for p in self.position:
            try:
                navigation = navigation[p]
            except KeyError as key_error:
                print("Error: malformed path looked up in console map")
                print(key_error)
                sys.exit(1)
        return navigation[action]


    def cd_into(self, dst):
        self.cd(["cd", dst[0]])


    def ls(self, cmd_args):
        for choice in self.choices():
            print_formatted_text(FormattedText([("fg:DimGrey", choice)]))


    def cd(self, cmd_args):
        if not len(cmd_args) == 2:
            print_formatted_text(FormattedText([("fg:Red", "Usage: cd <path>")]))
            return
        dst_dir = self.position.copy()
        for d in cmd_args[1].split("/"):
            if d == "":
                continue
            if d == "..":
                if len(dst_dir) > 1:
                    dst_dir.pop()
            else:
                dst_dir.append(d)
        if not self.dst_exists(dst_dir):
            print_formatted_text(FormattedText([("fg:Red", "Invalid path: {}".format(cmd_args[1]))]))
            return
        self.position = dst_dir
        self.print_path()


    def choices(self):
        navigation = self.navigation.copy()
        for p in self.position:
            try:
                navigation = navigation[p]
            except KeyError as key_error:
                print("Error: malformed path looked up in console map")
                print(key_error)
                sys.exit(1)
        return navigation.keys()


    def is_dir(self, cmd):
        # Currently this works because the navigation is three levels deep before
        # getting to actions. Need to find a better way which uses type information
        return len(self.position) < 3

    def dst_exists(self, dst):
        if len(dst) > 3:
            return False

        navigation = self.navigation.copy()
        for d in dst:
            try:
                navigation = navigation[d]
            except KeyError as key_error:
                return False
        return True


    def print_path(self):
        path = "".join([position_bit + " > " for position_bit in self.position])
        return print_formatted_text(FormattedText([("fg:Orange", path)]))


class ConsoleRunner():
    def __init__(self):
        self.console = Console(["aws"])
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

    def navigate(self):
        session = PromptSession(
            history=InMemoryHistory(),
            auto_suggest=AutoSuggestFromHistory(),
            enable_history_search=True,
            completer=None,
        )
        while True:
            try:
                cmd = session.prompt(self.console.prompt, placeholder=None)
                self.console.cmd(cmd)
            except CommandNotFoundError as command_not_found_error:
                print_formatted_text(FormattedText([("fg:Red", str(command_not_found_error))]))
                continue
            except KeyboardInterrupt:
                continue  # Control-C pressed. Try again.
            except EOFError:
                break  # Control-D pressed.

    def exit(self):
        clear_title()
        print("GoodBye!")


if __name__ == '__main__':
    console_runner = ConsoleRunner()
    console_runner.navigate()
    console_runner.exit()
