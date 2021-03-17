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

#from config import DefaultConfig

from botbuilder.dialogs.choices import Choice, ListStyle
from botbuilder.core import MessageFactory, UserState

from data_models import UserProfile
from calcolo_importo_recognizer import CalcoloImportoRecognizer
from dialogs.calcolo_dialog import CalcoloDialog
from dialogs.cancella_dialogo import CancellaDialogo

from dialogs.waterfall_query import WaterfallQuery
from dialogs.waterfall_text import WaterfallText
from dialogs.waterfall_photo import WaterfallPhoto
from config import DefaultConfig

import datetime

class WaterfallMain(ComponentDialog):
    def __init__(self, user_state: UserState):
        super(WaterfallMain, self).__init__(WaterfallMain.__name__)
    
        self.user_profile_accessor = user_state.create_property("UserProfile")

        luisRecognizer = CalcoloImportoRecognizer(configuration=DefaultConfig)
        calcoloDialog = CalcoloDialog()
        cancellaDialogo = CancellaDialogo()
        
        self.add_dialog(WaterfallQuery(luis_recognizer=luisRecognizer, calcolo_dialog=calcoloDialog, cancella_dialogo=cancellaDialogo))
        self.add_dialog(WaterfallPhoto(WaterfallPhoto.__name__))
        self.add_dialog(WaterfallText(WaterfallText.__name__))

        self.add_dialog(
            WaterfallDialog(
                WaterfallDialog.__name__,
                [
                    self.what_step,
                    self.summary_step,
                    self.replace_step,
                ],
            )
        )
        
        self.add_dialog(ChoicePrompt(ChoicePrompt.__name__))
        

        self.initial_dialog_id = WaterfallDialog.__name__

    async def what_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        return await step_context.prompt(
            ChoicePrompt.__name__,
            PromptOptions(
                prompt=MessageFactory.text(f"Ciao, cosa vuoi fare?"),
                choices=[Choice("Aggiungi fattura manualmente"), Choice("Aggiungi foto fattura"), Choice("Operazioni")],
                style=ListStyle.hero_card
            ),
        )  


    async def summary_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        
        result = step_context.result.value
        

        if result == "Aggiungi fattura manualmente":
            return await step_context.begin_dialog(WaterfallText.__name__)
        elif result == "Aggiungi foto fattura":
            return await step_context.begin_dialog(WaterfallPhoto.__name__)
        elif result == "Operazioni":
            
            return await step_context.begin_dialog(WaterfallQuery.__name__)
        else:
            return await step_context.replace_dialog(WaterfallMain.__name__)

        return await step_context.replace_dialog(WaterfallDialog.__name__)    

    async def replace_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:

        return await step_context.replace_dialog(WaterfallDialog.__name__)    

    