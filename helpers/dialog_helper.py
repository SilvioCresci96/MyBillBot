# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
from botbuilder.core import StatePropertyAccessor, TurnContext, MessageFactory, CardFactory
from botbuilder.dialogs import Dialog, DialogSet, DialogTurnStatus
from botbuilder.schema import (
    ActionTypes,
    Attachment,
    HeroCard,
)
from config import DefaultConfig


class DialogHelper:
    @staticmethod
    async def run_dialog(
        dialog: Dialog, turn_context: TurnContext, accessor: StatePropertyAccessor
    ):
        dialog_set = DialogSet(accessor)
        dialog_set.add(dialog)

        dialog_context = await dialog_set.create_context(turn_context)
        if turn_context.activity.text == "/stop":
            await dialog_context.cancel_all_dialogs()
        
        elif turn_context.activity.text == "/start":
            await turn_context.send_activity(MessageFactory.attachment(CardFactory.hero_card(HeroCard(
                text="Benvenuto in MyBillBot. Attraverso questo bot è possibile tenere traccia del proprio fatturato e richiedere in qualsiasi momento il fatturato di uno specifico giorno o di un certo periodo.\nAll'inizio della conversazione si hanno 3 opzioni:\n1. Aggiungere fattura manualmente: vi sarà richiesto di inserire l'importo da salvare e la data da associare a tale importo.\n2. Aggiungi foto fattura: vi sarà richiesto di inviare una foto dello scontrino di chiusura cassa in modo che provvederò io a ricavarmi l'importo e la data da salvare.\n3. Operazione: in questa sezione puoi chiedermi il fatturato di un giorno specifico o il fatturato di un intero mese. Puoi usare questa sezione anche per richiedere che venga eliminata una fattura in una particolare data in modo che non ne terrò conto per calcoli futuri.\n\n Inizia subito a tenere traccia del tuo fatturato!\nInvia un qualsiasi messaggio per iniziare. "
            ))))
        else:
            results = await dialog_context.continue_dialog()
            if results.status == DialogTurnStatus.Empty:
                await dialog_context.begin_dialog(dialog.id)


