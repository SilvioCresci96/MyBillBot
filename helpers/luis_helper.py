# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
from enum import Enum
from typing import Dict
from botbuilder.ai.luis import LuisRecognizer
from botbuilder.core import IntentScore, TopIntent, TurnContext

from invoice_details import InvoiceDetails


class Intent(Enum):
    CALCOLO_IMPORTO = "CalcoloImporto"
    CANCEL = "CancellaImporto"
    GET_WEATHER = "GetWeather"
    NONE_INTENT = "NoneIntent"


def top_intent(intents: Dict[Intent, dict]) -> TopIntent:
    max_intent = Intent.NONE_INTENT
    max_value = 0.0

    for intent, value in intents:
        intent_score = IntentScore(value)
        if intent_score.score > max_value:
            max_intent, max_value = intent, intent_score.score

    return TopIntent(max_intent, max_value)


class LuisHelper:
    @staticmethod
    async def execute_luis_query(
        luis_recognizer: LuisRecognizer, turn_context: TurnContext
    ) -> (Intent, object):
        """
        Returns an object with preformatted LUIS results for the bot's dialogs to consume.
        """
        result = None
        intent = None

        try:
            recognizer_result = await luis_recognizer.recognize(turn_context)

            intent = (
                sorted(
                    recognizer_result.intents,
                    key=recognizer_result.intents.get,
                    reverse=True,
                )[:1][0]
                if recognizer_result.intents
                else None
            )

            if intent == Intent.CALCOLO_IMPORTO.value:
                result = InvoiceDetails()

                # We need to get the result from the LUIS JSON which at every level returns an array.
                date_entities = recognizer_result.entities.get("$instance", {}).get(
                    "Data", []
                )
                if len(date_entities) > 0:
                    if recognizer_result.entities.get("Data", [{"$instance": {}}])[0][0]:
                        result.date = date_entities[0]["text"].capitalize()

                periodo_entities = recognizer_result.entities.get("$instance", {}).get(
                    "Periodo", []
                )
                if len(periodo_entities) > 0:
                    if recognizer_result.entities.get("Periodo", [{"$instance": {}}])[0][0]:
                        result.periodo = periodo_entities[0]["text"].capitalize()

            elif intent == Intent.CANCEL.value:
                result = InvoiceDetails()

                date_entities = recognizer_result.entities.get("$instance", {}).get(
                    "Data", []
                )
                if len(date_entities) > 0:
                    if recognizer_result.entities.get("Data", [{"$instance": {}}])[0][0]:
                        result.date = date_entities[0]["text"].capitalize()


                

        except Exception as exception:
            print(exception)

        return intent, result
