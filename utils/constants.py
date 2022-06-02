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

from typing import (
    Tuple,
)

__all__: Tuple[str, ...] = (
    'GENERAL_CHANNEL',
    'LOGGING_CHANNEL',
    'COACH_ROLE',
    'MOD_ROLE',
    'CAPTAIN_ROLE',
    'LOCKDOWN_ROLE',
    'LOCKDOWN_NOTIFICATIONS_ROLE',
    'BYPASS_FURY',
    'RL_ROLE',
    'LOL_ROLE',
    'SMASH_ROLE',
    'FORTNITE_ROLE',
    'OVERWATCH_ROLE',
    'FURY_GUILD',
    'NSFW_FILTER_CONSTANT',
    'MUTED_ROLE',
)

# Channels
GENERAL_CHANNEL = 881938845929730098
LOGGING_CHANNEL = 765631488506200115
MESSAGE_LOG_CHANNEL = 914773977463947284

# Threads
COUNTING_THREAD: int = 903700454532321290

# Roles
COACH_ROLE = 763517555833962586
MOD_ROLE = 763384816942448640
CAPTAIN_ROLE = 765360488816967722
LOCKDOWN_ROLE = 802304875266179073
LOCKDOWN_NOTIFICATIONS_ROLE = 867901004728762399
BYPASS_FURY = 802948019376488511
RL_ROLE = 763411805485531147
LOL_ROLE = 807406432764559370
SMASH_ROLE = 807395882358145076
FORTNITE_ROLE = 763411722081140776
OVERWATCH_ROLE = 807393744230809650
MUTED_ROLE = 888107749869756457
GAME_CONSULTANT_ROLE = 937861108960755743

# Guilds
FURY_GUILD = 757664675864248360

# Constants
NSFW_FILTER_CONSTANT = 0.80


# Emojis
BLOB_BAN: str = '<:blobban:981967066787614731>'
BLOB_SEENSOMESTUFF: str = '<:blobseensomestuff:981646175159603210>'
BLOB_PAIN: str = '<:blobpain:861430730018258965>'
NOT_LIKE_BLOB: str = '<:notlikeblob:883073333917261884>'
BLOB_UPSET: str = '<:blobupset:867429428439285781>'
BLOB_WEARY: str = '<:blobweary:867429471081857025>'
