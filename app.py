# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
import os
import sys
import uuid
import traceback
from datetime import datetime
from http import HTTPStatus
from typing import Dict
import json

from aiohttp import web
from aiohttp.web import Request, Response, json_response
from botbuilder.core import (
    BotFrameworkAdapter,
    BotFrameworkAdapterSettings,
    ConversationState,
    MemoryStorage,
    TurnContext,
    UserState,
)
from botbuilder.core.integration import aiohttp_error_middleware
from botbuilder.schema import Activity, ActivityTypes

from config import DefaultConfig
from dialogs.waterfall_query import WaterfallQuery
from bots.dialog_bot import DialogBot
from dialogs.waterfall_main import WaterfallMain
from botbuilder.schema import Activity, ActivityTypes, ConversationReference



CONFIG = DefaultConfig()

# Create adapter.
# See https://aka.ms/about-bot-adapter to learn more about how bots work.
SETTINGS = BotFrameworkAdapterSettings(CONFIG.APP_ID, CONFIG.APP_PASSWORD)
ADAPTER = BotFrameworkAdapter(SETTINGS)


# Catch-all for errors.
async def on_error(context: TurnContext, error: Exception):
    # This check writes out errors to console log
    # NOTE: In production environment, you should consider logging this to Azure
    #       application insights.
    print(f"\n [on_turn_error]: { error }", file=sys.stderr)
    traceback.print_exc()

    # Send a message to the user
    await context.send_activity("The bot encountered an error or bug.")
    await context.send_activity(
        "To continue to run this bot, please fix the bot source code."
    )
    # Send a trace activity if we're talking to the Bot Framework Emulator
    if context.activity.channel_id == "emulator":
        # Create a trace activity that contains the error object
        trace_activity = Activity(
            label="TurnError",
            name="on_turn_error Trace",
            timestamp=datetime.utcnow(),
            type=ActivityTypes.trace,
            value=f"{error}",
            value_type="https://www.botframework.com/schemas/error",
        )

        # Send a trace activity, which will be displayed in Bot Framework Emulator
        await context.send_activity(trace_activity)

    # Clear out state
    await CONVERSATION_STATE.delete(context)


# Set the error handler on the Adapter.
# In this case, we want an unbound method, so MethodType is not needed.
ADAPTER.on_turn_error = on_error

# Create a shared dictionary.  The Bot will add conversation references when users
# join the conversation and send messages.
CONVERSATION_REFERENCES: Dict[str, ConversationReference] = dict()

# Create MemoryStorage, UserState and ConversationState
MEMORY = MemoryStorage()
CONVERSATION_STATE = ConversationState(MEMORY)
USER_STATE = UserState(MEMORY)

# create main dialog and bot
DIALOG = WaterfallMain(USER_STATE)
BOT = DialogBot(CONVERSATION_STATE, USER_STATE, DIALOG, CONVERSATION_REFERENCES)

APP_ID = SETTINGS.app_id if SETTINGS.app_id else uuid.uuid4()


# If the channel is the Emulator, and authentication is not in use, the AppId will be null.
# We generate a random AppId for this case only. This is not required for production, since
# the AppId will have a value.
#APP_ID = SETTINGS.app_id if SETTINGS.app_id else uuid.uuid4()

# Listen for incoming requests on /api/messages.
async def messages(req: Request) -> Response:

    if "application/json" in req.headers["Content-Type"]:
        body = await req.json()
    else:
        return Response(status=HTTPStatus.UNSUPPORTED_MEDIA_TYPE)

    activity = Activity().deserialize(body)
    auth_header = req.headers["Authorization"] if "Authorization" in req.headers else ""

    response = await ADAPTER.process_activity(activity, auth_header, BOT.on_turn)
    if response:
        return json_response(data=response.body, status=response.status)
    return Response(status=HTTPStatus.OK)


# Listen for requests on /api/notify, and send a messages to all conversation members.
async def notify(req: Request) -> Response:  # pylint: disable=unused-argument
    intera = req.query_string
    separatore = intera.index('&media=')
    id_utente = intera[:separatore]
    media = intera[separatore+7:]
    await _send_proactive_message(userID = id_utente, tot= media)
    return Response(status=HTTPStatus.OK, text=f"La media del fatturato del mese scorso è di {req.query_string}€ al giorno!")


# Send a message to all conversation members.
# This uses the shared Dictionary that the Bot adds conversation references to.
async def _send_proactive_message(userID: str = None, tot : str = None):
    for conversation_reference in CONVERSATION_REFERENCES.values():
        user_id = conversation_reference.user.id
        if user_id == userID:
            await ADAPTER.continue_conversation(
                conversation_reference,
                lambda turn_context: turn_context.send_activity(f"La media del fatturato del mese scorso è di {tot}€ al giorno!"),
                APP_ID,
            )

def init_func(argv):
    APP = web.Application(middlewares=[aiohttp_error_middleware])
    APP.router.add_post("/api/messages", messages)
    APP.router.add_get("/api/notify", notify)

    return APP

if __name__ == "__main__":
    APP = init_func(None)
    try:
        web.run_app(APP, host="localhost", port=CONFIG.PORT)
    except Exception as error:
        raise error

