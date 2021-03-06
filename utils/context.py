"""
The MIT License (MIT)

Copyright (c) 2020-present NextChai

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""
from __future__ import annotations

"""
Mozilla Public License Version 2
================================

Copyright (c) 2016-present Rapptz

Full copyright can be found here: https://github.com/Rapptz/RoboDanny/blob/rewrite/LICENSE.txt

Please note this only applies to the "tick" function.
"""

import asyncio
from typing import Any, Callable, Dict, Optional, Tuple, Union, TYPE_CHECKING, TypeVar
from typing_extensions import Self

import discord
from discord.ext import commands

if TYPE_CHECKING:
    from bot import DiscordBot, FuryBot

__all__ = (
    'Confirmation',
    'Context',
    'tick',
)

FuryT = TypeVar('FuryT', bound='DiscordBot')


def tick(opt: Optional[bool], label: Optional[str] = None) -> str:
    """Used to tick a message based on the operation.

    Parameters
    ----------
    opt: Optional[:class:`bool`]
        The operation to tick.
    label: Optional[:class:`str`]
        A label for the tick, if any.

    Returns
    -------
    :class:`str`
        The ticked message.
    """
    lookup = {
        True: '???',
        False: '???',
        None: '???',
    }
    emoji = lookup.get(opt, '???')

    if label is not None:
        return f'{emoji}: {label}'

    return emoji


class Confirmation(discord.ui.View):
    """Used to get confirmation from the user in a simple way.

    Attributes
    ----------
    value: :class:`bool`
        Denotes if the user has confirmed to the operation.
    author: Union[:class:`discord.Member`, :class:`discord.User`]
        The user who is confirming the operation.
    """

    __slots__: Tuple[str, ...] = ('value', 'author')

    def __init__(self, author: Union[discord.Member, discord.User]):
        super().__init__()
        self.value: bool = False
        self.author: Union[discord.Member, discord.User] = author

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """|coro|

        A coroutine that is called to check if the interaction is valid.

        Parameters
        ----------
        interaction: :class:`discord.Interaction`
            The interaction to check.

        Returns
        -------
        :class:`bool`
            Whether the interaction is valid.
        """
        result: bool = interaction.user == self.author
        if not result:
            await interaction.response.send_message('Hey! This isn\'t yours!', ephemeral=True)

        return result

    def _cleanup(self) -> None:
        for child in self.children:
            child.disabled = True  # type: ignore

    @discord.ui.button(label='Confirm', style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button[Self]) -> None:
        """|coro|

        The callback for the confirm button. When pressed, will set the internal
        marker to True and stop the view.

        Parameters
        ----------
        interaction: :class:`discord.Interaction`
            The interaction object.
        button: :class:`discord.ui.Button`
            The button that was pressed.
        """
        self._cleanup()
        self.stop()
        self.value = True

        await interaction.response.edit_message(view=self)
        await interaction.followup.send('Confirming', ephemeral=True)

    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.grey)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button[Self]):
        """|coro|

        The callback for the confirm button. When pressed, will set the internal
        marker to False and stop the view.

        Parameters
        ----------
        interaction: :class:`discord.Interaction`
            The interaction object.
        button: :class:`discord.ui.Button`
            The button that was pressed.
        """
        self._cleanup()
        self.stop()
        self.value = False

        await interaction.response.edit_message(view=self)
        await interaction.followup.send('Cancelled', ephemeral=True)


class DummyContext:
    """A dummy context used to convert human time without a context obj.

    Attributes
    ----------
    created_at: :class:`datetime.datetime`
        When the context was created.
    """

    __slots__: Tuple[str, ...] = ('message',)

    def __init__(self) -> None:
        self.message = type('DummyContext', (object,), {'created_at': discord.utils.utcnow()})

    def __repr__(self) -> str:
        return '<DummyContext created_at={0.created_at}>'.format(self)


class Context(commands.Context['FuryBot']):
    """The overridden Context class. Used to provide some simple
    functionality to the bot, which can home in handy for commands.
    """

    __slots__: Tuple[str, ...] = ()

    if TYPE_CHECKING:
        bot: FuryBot

    async def get_confirmation(self, *args: Any, **kwargs: Any) -> bool:
        """Get confirmation fromt he user.

        Parameters
        ----------
        args: List[Any]
            The args to pass onto the send function.
        kwargs: Dict[str, Any]
            The kwargs to pass onto the send function.

        Returns
        -------
        :class:`bool`
            True if confirmation was "Confirm" and false if confirmation was "Cancel".
        """
        view = Confirmation(author=self.author)
        kwargs['view'] = view

        await self.send(*args, **kwargs)
        await view.wait()

        return view.value

    def tick(self, opt: Optional[bool], label: Optional[str] = None) -> str:
        return tick(opt, label)

    async def send(self, *args: Any, **kwargs: Any) -> discord.Message:  # type: ignore
        if not kwargs.get('allowed_mentions', None):
            kwargs['allowed_mentions'] = discord.AllowedMentions.none()

        return await super().send(*args, **kwargs)

    async def prompt(
        self,
        content: Optional[str] = None,
        *,
        timeout: float = 60.0,
        check: Optional[Callable[[discord.Message], bool]] = None,
        destination: Optional[discord.abc.MessageableChannel] = None,
        delete_after: bool = False,
        **kwargs: Dict[Any, Any],
    ) -> Optional[discord.Message]:
        """|coro|

        Prompt the user with a question and get wait for a response.

        Parameters
        ----------
        content: :class:`str`
            The content to pass to :meth:`Context.send`.
        timeout: :class:`float`
            The max amount of time to wait for a response. If the user doesn't respond in time,
            the prompt will be cancelled.
        check: Callable[[:class:`discord.Message`], Optional[:class:`bool`]]
            A function used to check if the response is valid. If none is provided
            a default check will be used which checks for author and channel.
        destination: Optional[:class:`discord.abc.MessageableChannel`]
            The destination channel to send the prompt to. If none is provided,
            the context channel will be used.
        delete_after: :class:`bool`
            Whether to delete the message sent by the client after the user has finished responding.
            Defaults to ``False``.
        kwargs: Dict[str, Any]
            A dict of keyword arguments to pass to :meth:`Context.send`.

        Returns
        -------
        Optional[:class:`discord.Message`]
            The response message if the user responded, otherwise ``None``.
        """
        if not check:
            check = lambda message: message.channel == self.channel and message.author == self.author

        def wrapped_check(message: discord.Message) -> bool:
            if message.content is None:
                return check(message)

            if ('stop', 'no', 'abort', 'close', 'cancel', 'end', 'quit', 'none', 'n') in message.content.lower().split():
                raise TypeError('Aborted')

            return check(message)

        message = await (destination or self.channel).send(content, **kwargs)
        try:
            response = await self.bot.wait_for('message', check=wrapped_check, timeout=timeout)
        except asyncio.TimeoutError:
            await message.reply('Prompt timed out, you need to re-do this operation.')
            return None
        except TypeError:
            await message.reply('Aborted.')
            return None

        if delete_after:
            await message.delete()

        return response
