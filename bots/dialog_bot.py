# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from botbuilder.core import ActivityHandler, ConversationState, TurnContext, UserState
from botbuilder.dialogs import Dialog
from helpers.dialog_helper import DialogHelper
from botbuilder.schema import ChannelAccount, ConversationReference, Activity
from typing import Dict
import requests




class DialogBot(ActivityHandler):
    """
    This Bot implementation can run any type of Dialog. The use of type parameterization is to allows multiple
    different bots to be run at different endpoints within the same project. This can be achieved by defining distinct
    Controller types each with dependency on distinct Bot types. The ConversationState is used by the Dialog system. The
    UserState isn't, however, it might have been used in a Dialog implementation, and the requirement is that all
    BotState objects are saved at the end of a turn.
    """

    def __init__(
        self,
        conversation_state: ConversationState,
        user_state: UserState,
        dialog: Dialog,
        conversation_references: Dict[str, ConversationReference],
    ):
        self.conversation_references = conversation_references

        if conversation_state is None:
            raise TypeError(
                "[DialogBot]: Missing parameter. conversation_state is required but None was given"
            )
        if user_state is None:
            raise TypeError(
                "[DialogBot]: Missing parameter. user_state is required but None was given"
            )
        if dialog is None:
            raise Exception("[DialogBot]: Missing parameter. dialog is required")

        self.conversation_state = conversation_state
        self.user_state = user_state
        self.dialog = dialog

    async def on_turn(self, turn_context: TurnContext):
        await super().on_turn(turn_context)

        # Save any state changes that might have ocurred during the turn.
        await self.conversation_state.save_changes(turn_context)
        await self.user_state.save_changes(turn_context)

    async def on_message_activity(self, turn_context: TurnContext):
        self._add_conversation_reference(turn_context.activity)
        await DialogHelper.run_dialog(
            self.dialog,
            turn_context,
            self.conversation_state.create_property("DialogState"),
        )
    async def on_conversation_update_activity(self, turn_context: TurnContext):
        self._add_conversation_reference(turn_context.activity)
        return await super().on_conversation_update_activity(turn_context)


    async def on_members_added_activity(
        self, members_added: [ChannelAccount], turn_context: TurnContext
    ):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                
                await turn_context.send_activity(
                    "Benvenuto in MyBillBot. Attraverso questo bot è possibile tenere traccia del proprio fatturato e richiedere in qualsiasi momento il fatturato di uno specifico giorno o di un certo periodo.\nAll'inizio della conversazione si hanno 3 opzioni:\n1. Aggiungere fattura manualmente: vi sarà richiesto di inserire l'importo da salvare e la data da associare a tale importo.\n2. Aggiungi foto fattura: vi sarà richiesto di inviare una foto dello scontrino di chiusura cassa in modo che provvederò io a ricavarmi l'importo e la data da salvare.\n3. Operazione: in questa sezione puoi chiedermi il fatturato di un giorno specifico o il fatturato di un intero mese. Puoi usare questa sezione anche per richiedere che venga eliminata una fattura in una particolare data in modo che non ne terrò conto per calcoli futuri.\n\n Inizia subito a tenere traccia del tuo fatturato!"
                )
    
    def _add_conversation_reference(self, activity: Activity):
        """
        This populates the shared Dictionary that holds conversation references. In this sample,
        this dictionary is used to send a message to members when /api/notify is hit.
        :param activity:
        :return:
        """
        conversation_reference = TurnContext.get_conversation_reference(activity)
        self.conversation_references[
            conversation_reference.user.id
        ] = conversation_reference

