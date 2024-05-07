from __future__ import annotations

import contextlib
import sys
import textwrap
import traceback
import typing

import discord
from discord.ext import commands

from src import errors

if typing.TYPE_CHECKING:
    from src import Bot, Context

type Language = typing.Literal["py"]
type TerminalOutput = str | None
type UserMessage = str | None
type ErrorMessages = tuple[TerminalOutput, UserMessage]


class ErrorHandler(commands.Cog):
    async def on_error(self, error: str, *_args: typing.Any, **_kwargs: typing.Any):
        stack = traceback.format_exception(*sys.exc_info())

        print("An error occurred:\n\n", *stack, file=sys.stderr, sep="")

    def __init__(self, bot: "Bot"):
        _original_on_error = bot.on_error
        bot.on_error = self.on_error

        self.bot = bot

        self._original_on_error = _original_on_error
        self.ignored = (
            errors.CheckError,
            commands.CommandNotFound,
        )

    def teardown(self):
        self.bot.on_error = self._original_on_error

    def codeblock(self, code: str, *, language: Language | None = None):
        real_language = language or ""

        # fmt: off
        return (
            f"```{real_language}\n"
            f"{textwrap.dedent(code)}\n"
            "```"
        )
        # fmt: on

    def generate_general_error_messages(self, context: "Context", error: commands.CommandError) -> ErrorMessages:
        stack = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        header = "An error occurred"

        if context.command:
            header += f' when executing "{context.command.qualified_name}"'

        # fmt: off
        for_terminal = (
            f"{header}:\n"
            "\n"
            f"{stack}"
        )
        for_user = (
            f"{header}:\n" +
            self.codeblock(stack, language = "py")
        )
        # fmt: on

        return for_terminal, for_user

    def generate_ignore_error_messages(self, error: commands.CommandError) -> ErrorMessages:
        for_terminal = f"Ignoring error {error.__class__.__name__}"

        if addendum := getattr(error, "message", None):
            for_terminal += f" ({addendum})"

        return f"{for_terminal}...", None

    def generate_unavailable_feature_messages(self, context: "Context", error: errors.UnavailableFeature) -> ErrorMessages:
        for_terminal, _ = self.generate_ignore_error_messages(error)
        command_name = context.command.qualified_name if context.command else "unavailable"
        unavailable_dependencies = error.message

        # fmt: off
        for_user = (
            "This feature is currently unavailable due to a lack of dependencies. For more information, please screenshot "
            "this message in it's entirety and notify the developers by sending it, plus the command you tried to run, to "
            "them.\n"
            "\n"
            f"Unavailable dependencies for command `{command_name}`: `{unavailable_dependencies}`. Please enable these "
            "features to ensure the prior command becomes available."
        )
        # fmt: on

        return for_terminal, for_user

    async def try_report_error(self, context: "Context", for_terminal: TerminalOutput, for_user: UserMessage):
        if for_terminal is not None:
            print(for_terminal)

        if for_user is None:
            return

        try:
            with contextlib.suppress(discord.HTTPException):
                await context.send(for_user)
        except Exception as error:
            stack = traceback.format_exception(type(error), error, error.__traceback__)

            print(f"An error occurred when sending error message to user:\n\n", *stack, file=sys.stderr, sep="")

    @commands.Cog.listener()
    async def on_command_error(self, context: "Context", error: commands.CommandError):
        error = getattr(error, "original", error)
        terminal_output: TerminalOutput = None
        message: UserMessage = None

        if isinstance(error, errors.UnavailableFeature):
            terminal_output, message = self.generate_unavailable_feature_messages(context, error)
        elif isinstance(error, self.ignored):
            terminal_output, message = self.generate_ignore_error_messages(error)

        if not (terminal_output or message):
            terminal_output, message = self.generate_general_error_messages(context, error)

        await self.try_report_error(context, terminal_output, message)


COG: ErrorHandler | None = None


async def setup(bot: "Bot"):
    COG = ErrorHandler(bot)

    await bot.add_cog(COG)


async def teardown(bot: "Bot"):
    if not COG:
        return

    COG.teardown()
