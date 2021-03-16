# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from botbuilder.dialogs import (
    ComponentDialog,
    WaterfallDialog,
    WaterfallStepContext,
    DialogTurnResult,
)
from botbuilder.dialogs.prompts import (
    TextPrompt,
    NumberPrompt,
    ChoicePrompt,
    ConfirmPrompt,
    AttachmentPrompt,
    PromptOptions,
    PromptValidatorContext,
    DateTimePrompt,
)
from botbuilder.dialogs.choices import Choice
from botbuilder.core import MessageFactory, UserState
from botbuilder.schema import InputHints

from calcolo_importo_recognizer import CalcoloImportoRecognizer
from dialogs.cancella_dialogo import CancellaDialogo
from dialogs.calcolo_dialog import CalcoloDialog
from invoice_details import InvoiceDetails
from helpers.luis_helper import LuisHelper, Intent
from config import DefaultConfig

import datetime


class WaterfallQuery(ComponentDialog):
    def __init__(self, luis_recognizer: CalcoloImportoRecognizer, calcolo_dialog: CalcoloDialog, cancella_dialogo: CancellaDialogo):
        super(WaterfallQuery, self).__init__(WaterfallQuery.__name__)

        #self.user_profile_accessor = user_state.create_property("UserProfile")
        self._luis_recognizer = luis_recognizer
        self._calcolo_dialog_id = calcolo_dialog.id
        self._cancella_dialogo_id = cancella_dialogo.id
        
        self.add_dialog(cancella_dialogo)
        self.add_dialog(calcolo_dialog)

        self.add_dialog(
            WaterfallDialog(
                WaterfallDialog.__name__,
                [
                    self.domanda_step,
                    self.summary_step,
                ],
            )
        )
       
        self.add_dialog(TextPrompt(TextPrompt.__name__))
        #self.add_dialog(TextPrompt(TextPrompt.__name__, WaterfallQuery.insertCorrectdate))
        self.add_dialog(
            NumberPrompt(NumberPrompt.__name__)
        )
        self.add_dialog(ChoicePrompt(ChoicePrompt.__name__))
        self.add_dialog(ConfirmPrompt(ConfirmPrompt.__name__))
        """self.add_dialog(
            AttachmentPrompt(
                AttachmentPrompt.__name__, WaterfallQuery.picture_prompt_validator
            )
        )"""

        self.initial_dialog_id = WaterfallDialog.__name__
    
    async def domanda_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text("Cosa vuoi sapere?")),
        )
        return step_context.next(0)

    
   

    async def summary_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        if not self._luis_recognizer.is_configured:
        
            # LUIS is not configured, we just run the BookingDialog path with an empty BookingDetailsInstance.
            return await step_context.begin_dialog(
                self._calcolo_dialog_id, InvoiceDetails()
            )

        # Call LUIS and gather any potential booking details. (Note the TurnContext has the response to the prompt.)
        recognizer = CalcoloImportoRecognizer(configuration=DefaultConfig)
        intent, luis_result = await LuisHelper.execute_luis_query(recognizer, step_context.context)
        
        
        if intent == Intent.CALCOLO_IMPORTO.value and luis_result:

            return await step_context.begin_dialog(self._calcolo_dialog_id, luis_result)

        elif intent == Intent.CANCEL.value and luis_result:

            return await step_context.begin_dialog(self._cancella_dialogo_id, luis_result)


        else:
            didnt_understand_text = (
                "Sorry, I didn't get that. Please try asking in a different way"
            )
            didnt_understand_message = MessageFactory.text(
                didnt_understand_text, didnt_understand_text, InputHints.ignoring_input
            )
            await step_context.context.send_activity(didnt_understand_message)

        return await step_context.next(None)
        return await step_context.end_dialog()

    

