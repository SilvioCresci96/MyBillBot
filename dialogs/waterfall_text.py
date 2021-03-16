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
import requests
from data_models import UserProfile
import datetime

class WaterfallText(ComponentDialog):
    def __init__(self, dialog_id: str = None):
        super(WaterfallText, self).__init__(dialog_id or WaterfallText.__name__)
            
        self.add_dialog(
            WaterfallDialog(
                WaterfallDialog.__name__,
                [
                    
                    self.fatturatestuale_step,
                    self.date_step,
                    self.confirm_step,
                    self.insertdata_step,
                    self.summary_step,
                ],
            )
        )
        #self.add_dialog(TextPrompt(TextPrompt.__name__))
        self.add_dialog(TextPrompt(TextPrompt.__name__, WaterfallText.insertCorrectdate))
        self.add_dialog(
            NumberPrompt(NumberPrompt.__name__)
        )
        self.add_dialog(ChoicePrompt(ChoicePrompt.__name__))
        self.add_dialog(ConfirmPrompt(ConfirmPrompt.__name__))

        self.initial_dialog_id = WaterfallDialog.__name__
    

    async def fatturatestuale_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        return await step_context.prompt(
            NumberPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text("Per favore inserisci l'importo")),
        )
        return step_context.next(0)

    
    async def date_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        if step_context.result == "back":
            return await step_context.end_dialog()
            
        step_context.values["amount"] = step_context.result
        self.var = True
        return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(
                    prompt=MessageFactory.text("Per favore inserisci la data (DD-MM-YYYY)"),
                    retry_prompt=MessageFactory.text("Inserisci la data corretta (DD-MM-YYYY)"),)
            )


    async def confirm_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        step_context.values["date"] = step_context.result
        return await step_context.prompt(
            ConfirmPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text(f"Hai inserito l'importo: {step_context.values['amount']}€ nella data: {step_context.values['date']} è corretto?")),
        )


    async def insertdata_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        if step_context.result:
            r = requests.get(f"https://mybillbotfirstfunction.azurewebsites.net/api/first_function?id_utente={step_context.context.activity.from_property.id}&funct=insert&totale={step_context.values['amount']}&data={step_context.values['date']}")
            await step_context.context.send_activity("Ho caricato i dati da te inseriti")
            return await step_context.end_dialog()

        await step_context.context.send_activity("Prova a reinserire importo e data o decidi cosa vuoi fare")
        return await step_context.end_dialog()
        

    async def summary_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:

        return await step_context.end_dialog()


    @staticmethod
    async def insertCorrectdate(prompt_context: PromptValidatorContext) -> bool:
        try:
            datetime.datetime.strptime(prompt_context.recognized.value, "%d-%m-%Y")
        except ValueError:
            return False
        
        return True