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
)
from botbuilder.dialogs.choices import Choice
from botbuilder.core import MessageFactory, UserState

from io import BytesIO
import requests
import FormRecognizer
from datetime import datetime

class WaterfallPhoto(ComponentDialog):
    def __init__(self, dialog_id: str = None):
        super(WaterfallPhoto, self).__init__(dialog_id or WaterfallPhoto.__name__)

        #self.user_profile_accessor = user_state.create_property("UserProfile")
        self.add_dialog(
            WaterfallDialog(
                WaterfallDialog.__name__,
                [
                    self.picture_step,
                    self.confirm_step,
                    self.evaluate_data_step,
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
        self.add_dialog(
            AttachmentPrompt(
                AttachmentPrompt.__name__, WaterfallPhoto.picture_prompt_validator
            )
        )

        self.initial_dialog_id = WaterfallDialog.__name__

    
    async def picture_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        
        prompt_options = PromptOptions(
            prompt=MessageFactory.text(
                "Invia la foto dello scontrino di chiusura cassa in modo che totale giornaliero e data siano ben visibili (o invia un qualsiasi messaggio per tornare indietro)."
            ),
            retry_prompt=MessageFactory.text(
                "The attachment must be a jpeg/png image file."
            ),
            number_of_attempts=1
        )
        return await step_context.prompt(AttachmentPrompt.__name__, prompt_options)

    async def confirm_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        
        if step_context.result:
            image = step_context.result[0]
        res: Response = requests.get(image.content_url)

        await step_context.context.send_activity("Sto analizzando...")
        
        dati_scontrino = FormRecognizer.runAnalysis(input_file = BytesIO(res.content), file_type = image.content_type)

        if dati_scontrino is None:
            await step_context.context.send_activity("C'è stato un problema")
            return await step_context.end_dialog()
        
        step_context.values["dati_scontrino"] = dati_scontrino

        data = dati_scontrino['data']
        tempData = str(data).replace("-","")
        data = datetime.strptime(tempData, '%Y%m%d').strftime('%d-%m-%Y')

        # WaterfallStep always finishes with the end of the Waterfall or
        # with another dialog; here it is a Prompt Dialog.
        return await step_context.prompt(
            ConfirmPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text(f"Dalla foto ho rilevato l'importo {dati_scontrino['totale']}€ in data {data} è corretto?")),
        )

    async def evaluate_data_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        if step_context.result:
            dati_scontrino = step_context.values["dati_scontrino"]

            data = dati_scontrino['data']
            tempData = str(data).replace("-","")
            data = datetime.strptime(tempData, '%Y%m%d').strftime('%d-%m-%Y')

            r = requests.get(f"https://mybillbotfirstfunction.azurewebsites.net/api/first_function?id_utente={step_context.context.activity.from_property.id}&funct=insert&totale={dati_scontrino['totale']}&data={data}")
            await step_context.context.send_activity("Ho caricato i dati da te inseriti")
            return await step_context.end_dialog()
            
        else:
            await step_context.context.send_activity("Prova a reinviare la foto")
            return await step_context.end_dialog()


    async def summary_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        #FormRecognizer.main([r"C:\Users\silvi\Desktop\Università\Cloud\test\1.jpeg"])
        return await step_context.end_dialog()


    @staticmethod
    async def picture_prompt_validator(prompt_context: PromptValidatorContext) -> bool:
        if not prompt_context.recognized.succeeded:
            await prompt_context.context.send_activity(
                "No attachments received. Proceeding without a profile picture..."
            )

            # We can return true from a validator function even if recognized.succeeded is false.
            return False 

        attachments = prompt_context.recognized.value

        valid_images = [
            attachment
            for attachment in attachments
            if attachment.content_type in ["image/jpeg", "image/png"]
        ]

        prompt_context.recognized.value = valid_images

        # If none of the attachments are valid images, the retry prompt should be sent.
        return len(valid_images) > 0

    
