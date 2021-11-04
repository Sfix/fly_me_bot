"""Class to read the data for LUIS and create the json to train and test."""

# Load the libriries
from typing import Dict
from typing import List
from typing import Union

import os
import json
import pandas as pd
import random

from shared_code.constants.files import FILES
from shared_code.constants.utterances import UTTERANCES
from shared_code.constants.luis_app import LUIS_APPS


class Frames:
    """Read the json and create the json needed for LUIS."""

    def __init__(self) -> None:
        """Init the class."""
        self.__df_raw_data: pd.DataFrame = self.__load_raw_data()
        self.__df_utterances: pd.DataFrame = self.get_df_utterances()
        self.__df_train_test: pd.DataFrame = self.__get_train_test_sets()

    #
    # Private
    #
    def __load_raw_data(self) -> pd.DataFrame:
        """Load the raw data.

        Returns:
            pd.DataFrame: the json in a pandas dataframe.
        """
        with open(file=FILES.FRAME_RAW_DATA, mode="r", encoding="utf-8") as handler:
            json_raw_data = json.load(handler)
        return pd.DataFrame(data=json_raw_data)

    def __decode_raw_acts(self, acts: List) -> List:
        """Decode the turns and retrieve the Entities.

        Args:
            turn (List): A full dialog.

        Returns:
            List: The turn by turn information.
        """
        from_date = None
        to_date = None
        from_place = None
        to_place = None
        max_budget = None
        for act in acts:
            if act["name"] != "inform":
                continue
            for arg in act["args"]:
                if arg["key"] == UTTERANCES.ENTITY_FROM_PLACE_IN_FRAMES:
                    from_place = arg["val"]
                elif arg["key"] == UTTERANCES.ENTITY_TO_PLACE_IN_FRAMES:
                    to_place = arg["val"]
                elif arg["key"] == UTTERANCES.ENTITY_FROM_DATE_IN_FRAMES:
                    from_date = arg["val"]
                elif arg["key"] == UTTERANCES.ENTITY_TO_DATE_IN_FRAMES:
                    to_date = arg["val"]
                elif arg["key"] == UTTERANCES.ENTITY_MAX_BUDGET_IN_FRAMES:
                    max_budget = arg["val"]
        return {
            UTTERANCES.ENTITY_FROM_PLACE: from_place,
            UTTERANCES.ENTITY_TO_PLACE: to_place,
            UTTERANCES.ENTITY_FROM_DATE: from_date,
            UTTERANCES.ENTITY_TO_DATE: to_date,
            UTTERANCES.ENTITY_MAX_BUDGET: max_budget,
        }

    def __decode_raw_turns(self, turns: List) -> List:
        """Decode the turns and retrieve the Entities.

        Args:
            turn (List): A full dialog.

        Returns:
            List: The turn by turn information.
        """
        decoded_acts = [
            self.__decode_raw_acts(turn["labels"]["acts"])
            if turn["author"] == "user"
            else {}
            for turn in turns
        ]
        return [
            {
                "text": turns[n]["text"],
                "author": turns[n]["author"],
                UTTERANCES.ENTITY_FROM_PLACE: decoded_acts[n][
                    UTTERANCES.ENTITY_FROM_PLACE
                ],
                UTTERANCES.ENTITY_TO_PLACE: decoded_acts[n][UTTERANCES.ENTITY_TO_PLACE],
                UTTERANCES.ENTITY_FROM_DATE: decoded_acts[n][
                    UTTERANCES.ENTITY_FROM_DATE
                ],
                UTTERANCES.ENTITY_TO_DATE: decoded_acts[n][UTTERANCES.ENTITY_TO_DATE],
                UTTERANCES.ENTITY_MAX_BUDGET: decoded_acts[n][
                    UTTERANCES.ENTITY_MAX_BUDGET
                ],
            }
            for n in range(len(turns))
            if turns[n]["author"] == "user"
        ]

    def __decode_raw_data(self, row) -> Dict[str, Union[str, int, float, None]]:
        """Decode a line of Frames.

        Args:
            row (Dict): one line of the raw data.

        Returns:
            Dict[str, Union[str, int, float, None]]: Decoded row for Utterances.
        """
        rating = (
            row["labels"]["userSurveyRating"]
            if row["labels"]["wizardSurveyTaskSuccessful"]
            else -row["labels"]["userSurveyRating"]
        )
        turns = self.__decode_raw_turns(row["turns"])
        return [
            {
                "id": row["id"],
                "rating": rating,
                "text": decoded_turn["text"],
                UTTERANCES.ENTITY_FROM_PLACE: decoded_turn[
                    UTTERANCES.ENTITY_FROM_PLACE
                ],
                UTTERANCES.ENTITY_TO_PLACE: decoded_turn[UTTERANCES.ENTITY_TO_PLACE],
                UTTERANCES.ENTITY_FROM_DATE: decoded_turn[UTTERANCES.ENTITY_FROM_DATE],
                UTTERANCES.ENTITY_TO_DATE: decoded_turn[UTTERANCES.ENTITY_TO_DATE],
                UTTERANCES.ENTITY_MAX_BUDGET: decoded_turn[
                    UTTERANCES.ENTITY_MAX_BUDGET
                ],
            }
            for decoded_turn in turns
        ]

    def __get_train_test_sets(self) -> pd.DataFrame:
        """Load or create the sets for tests and training.

        Returns:
            pd.DataFrame: pandas DataFrame with the information regarding the sets
        """
        if os.path.isfile(FILES.SAVED_UTTERANCES_TRAIN_TEST_SETS):
            return pd.read_pickle(FILES.SAVED_UTTERANCES_TRAIN_TEST_SETS)
        # Need to create the sets
        values_for_df = {
            "ok for training": len(self.__df_utterances) * [False],
            "ok for test": len(self.__df_utterances) * [False],
            "used for training": len(self.__df_utterances) * [False],
            "used for testing": len(self.__df_utterances) * [False],
            UTTERANCES.ENTITY_FROM_PLACE: len(self.__df_utterances) * [False],
            UTTERANCES.ENTITY_TO_PLACE: len(self.__df_utterances) * [False],
            UTTERANCES.ENTITY_FROM_DATE: len(self.__df_utterances) * [False],
            UTTERANCES.ENTITY_TO_DATE: len(self.__df_utterances) * [False],
        }
        df_train_test = pd.DataFrame(values_for_df, index=self.__df_utterances.index)

        # We keep 10% for testing
        for n in range(-5, 6):
            mask = (self.__df_utterances["rating"] >= n) & (
                self.__df_utterances["rating"] < n + 1
            )
            valid_indexes = list(self.__df_utterances.loc[mask.values].index)
            if not valid_indexes:
                continue
            random.shuffle(valid_indexes)
            index_for_test = random.sample(
                valid_indexes, max(1, int(0.1 * len(valid_indexes)))
            )
            df_train_test.loc[index_for_test, "ok for test"] = True
            index_for_training = [
                index for index in valid_indexes if index not in index_for_test
            ]
            df_train_test.loc[index_for_training, "ok for training"] = True

        # Add columns for entity
        df_train_test[UTTERANCES.ENTITY_FROM_PLACE] = self.__df_utterances[
            UTTERANCES.ENTITY_FROM_PLACE
        ].notnull()
        df_train_test[UTTERANCES.ENTITY_TO_PLACE] = self.__df_utterances[
            UTTERANCES.ENTITY_TO_PLACE
        ].notnull()
        df_train_test[UTTERANCES.ENTITY_FROM_DATE] = self.__df_utterances[
            UTTERANCES.ENTITY_FROM_DATE
        ].notnull()
        df_train_test[UTTERANCES.ENTITY_TO_DATE] = self.__df_utterances[
            UTTERANCES.ENTITY_TO_DATE
        ].notnull()
        df_train_test[UTTERANCES.ENTITY_MAX_BUDGET] = self.__df_utterances[
            UTTERANCES.ENTITY_MAX_BUDGET
        ].notnull()
        df_train_test.to_pickle(path=FILES.SAVED_UTTERANCES_TRAIN_TEST_SETS)
        return df_train_test

    def __find_positions(
        self, text: str, word: str, list_of_prewords: List[str]
    ) -> Dict[str, int]:
        """Find the start and end of the entity.

        arguments:
            text [str] : the sentence to search into.
            word [str] : the word to look at.
            list_of_prewords [list[str]]: the preword to use.

        Returns:
            Dict : startPos and endPos for the word with preword.
        """
        startPos = text.find(word)
        endPos = min(startPos + len(word), len(text))
        for preword in list_of_prewords:
            preword_position = text[:startPos].rfind(preword)
            if preword_position == -1:
                continue
            if text[preword_position + len(preword) : startPos].isspace():
                startPos = preword_position
                break
        return {"startPos": startPos, "endPos": endPos - 1}

    def __create_json_for_utterance(self, sample: int) -> json:
        """Create the json that defines an utterance.

        Args:
            sample (int): index of the utterance in __df_utterances

        Returns:
            json: the json that defines the utterance.
        """
        text = self.__df_utterances.loc[sample, "text"]
        result = {
            "text": text,
            "intent": LUIS_APPS.INTENTS["Specify journey name"],
            "entities": [],
        }
        data_entities = self.__df_utterances.loc[sample]
        values_for_loop = [
            {
                "file_prewords": FILES.WORDS_MAKING_ORIGIN,
                "entity_name": UTTERANCES.ENTITY_FROM_PLACE,
            },
            {
                "file_prewords": FILES.WORDS_MAKING_DESTINATION,
                "entity_name": UTTERANCES.ENTITY_TO_PLACE,
            },
            {
                "file_prewords": FILES.WORDS_MAKING_START,
                "entity_name": UTTERANCES.ENTITY_FROM_DATE,
            },
            {
                "file_prewords": FILES.WORDS_MAKING_END,
                "entity_name": UTTERANCES.ENTITY_TO_DATE,
            },
        ]
        for value in values_for_loop:
            entry = data_entities[value["entity_name"]]
            if type(entry) == str:
                with open(
                    file=os.path.join(FILES.PATH_TO_DATA, value["file_prewords"]),
                    mode="r",
                ) as file_handler:
                    json_data = json.load(file_handler)
                positions = self.__find_positions(
                    text=text, word=entry, list_of_prewords=json_data["list"]
                )
                if (positions["startPos"] == -1) | (positions["endPos"] == -1):
                    continue
                result["entities"].append(
                    {
                        "entity": value["entity_name"],
                        "startPos": positions["startPos"],
                        "endPos": positions["endPos"],
                        "children": [],
                    }
                )
        entry = data_entities[UTTERANCES.ENTITY_MAX_BUDGET]
        if type(entry) == str:
            positions = self.__find_positions(
                text=text, word=entry, list_of_prewords=[]
            )
            if (positions["startPos"] != -1) & (positions["endPos"] != -1):
                result["entities"].append(
                    {
                        "entity": "Max budget",
                        "startPos": positions["startPos"],
                        "endPos": positions["endPos"],
                        "children": [],
                    }
                )
        return result

    #
    # Public
    #
    def get_df_utterances(self) -> pd.DataFrame:
        """Create the DataFrame of the utterances.

        Returns:
            pd.DataFrame: Dataframe with the text and the entities
        """
        decoded_raw_data = [
            element
            for value in [
                self.__decode_raw_data(row)
                for _, row in self.__df_raw_data.iterrows()
                if row["labels"]["userSurveyRating"] is not None
            ]
            for element in value
        ]
        return pd.DataFrame(decoded_raw_data)

    @property
    def df_utterances(self) -> pd.DataFrame:
        """Return the DataFrame of utterances.

        Returns:
            pd.DataFrame: pandas dataframe of the user's utterances
        """
        return self.__df_utterances

    def get_train(
        self,
        total: int = 10,
        want_origin: bool = True,
        want_destination: bool = True,
        want_starting: bool = True,
        want_ending: bool = True,
        want_budget: bool = True,
        must_be_new: bool = True,
    ) -> json:
        """Provide a json of utterances for training.

        Args:
            total (int, optional)             : number of utterances wanted. Defaults to 10.
            want_Origin (bool, optional)      : need data with entity Origin. Defaults to True.
            want_Destination (bool, optional) : need data with entity Destination. Defaults to True.
            want_starting (bool, optional)    : need data with entity Starting. Defaults to True.
            want_ending (bool, optional)      : need data with entity Ending. Defaults to True.
            want_budget (bool, optional)      : need data with entity Budget. Defaults to True.
            must_be_new (bool, optional)      : need data not used at this point. Defaults to True.

        Returns:
            json: json of the utterances
        """
        mask = self.__df_train_test["ok for training"] != False
        if must_be_new:
            mask &= self.__df_train_test["used for training"] == False
        if want_origin:
            mask &= self.__df_train_test[UTTERANCES.ENTITY_FROM_PLACE]
        if want_destination:
            mask &= self.__df_train_test[UTTERANCES.ENTITY_TO_PLACE]
        if want_starting:
            mask &= self.__df_train_test[UTTERANCES.ENTITY_FROM_DATE]
        if want_ending:
            mask &= self.__df_train_test[UTTERANCES.ENTITY_TO_DATE]
        if want_budget:
            mask &= self.__df_train_test[UTTERANCES.ENTITY_MAX_BUDGET]
        # Take the best ratings
        for n in range(5, -6, -1):
            tmp_mask = mask & (self.__df_utterances["rating"] >= n)
            if sum(tmp_mask) >= total:
                mask = tmp_mask
                break
        if sum(mask) == 0:
            raise ("Pb. pas assez de données")
        indexes = list(self.__df_utterances.loc[mask].index)
        random.shuffle(indexes)
        samples = random.sample(indexes, min(len(indexes), total))
        self.__df_train_test.loc[indexes, "used for training"] = True
        return [self.__create_json_for_utterance(sample) for sample in samples]

    def get_test(
        self,
        total: int = 10,
        want_origin: bool = True,
        want_destination: bool = True,
        want_starting: bool = True,
        want_ending: bool = True,
        want_budget: bool = True,
        must_be_new: bool = True,
    ) -> json:
        """Provide a json of utterances for testing.

        Args:
            total (int, optional)             : number of utterances wanted. Defaults to 10.
            want_Origin (bool, optional)      : need data with entity Origin. Defaults to True.
            want_Destination (bool, optional) : need data with entity Destination. Defaults to True.
            want_starting (bool, optional)    : need data with entity Starting. Defaults to True.
            want_ending (bool, optional)      : need data with entity Ending. Defaults to True.
            want_budget (bool, optional)      : need data with entity Budget. Defaults to True.
            must_be_new (bool, optional)      : need data not used at this point. Defaults to True.

        Returns:
            json: json of the utterances
        """
        mask = self.__df_train_test["ok for test"] != False
        if must_be_new:
            mask &= self.__df_train_test["used for testing"] == False
        if want_origin:
            mask &= self.__df_train_test[UTTERANCES.ENTITY_FROM_PLACE]
        if want_destination:
            mask &= self.__df_train_test[UTTERANCES.ENTITY_TO_PLACE]
        if want_starting:
            mask &= self.__df_train_test[UTTERANCES.ENTITY_FROM_DATE]
        if want_ending:
            mask &= self.__df_train_test[UTTERANCES.ENTITY_TO_DATE]
        if want_budget:
            mask &= self.__df_train_test[UTTERANCES.ENTITY_MAX_BUDGET]
        # Take the best ratings
        if sum(mask) == 0:
            raise ("Pb. pas assez de données")
        for n in range(5, -6, -1):
            tmp_mask = mask & (self.__df_utterances["rating"] >= n)
            if sum(tmp_mask) >= total:
                mask = tmp_mask
                break
        indexes = list(self.__df_utterances.loc[mask].index)
        random.shuffle(indexes)
        samples = random.sample(indexes, min(len(indexes), total))
        self.__df_train_test.loc[indexes, "used for testing"] = True
        return [self.__create_json_for_utterance(sample) for sample in samples]


# Create a mean for debug
if __name__ == "__main__":
    frame = Frames()
    dt_train_set = frame.get_train()
    print(dt_train_set)
    print(len(dt_train_set))
