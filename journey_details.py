"""Handle the informations regarding the journey."""
from botbuilder.core import ActivityHandler, TurnContext, StoreItem, MemoryStorage

class  UtteranceLog(StoreItem):
    """Class for storing a log of utterances (text of messages) as a list."""

    def __init__(self):
        """Initialise the class."""
        super(UtteranceLog, self).__init__()
        self.utterance_list = []
        self._turn_number = 0
        self.e_tag = "*"

    @property
    def turn_number(self):
        """Define the getter."""
        return self._turn_number

    @turn_number.setter
    def turn_number(self, value):
        """Define the setter."""
        self._turn_number = value


class Journey_details:
    """Handle the details for our journey."""
    def __init__(
        self,
        destination: str = None,
        origin: str = None,
        departure_date: str = None,
        return_date: str = None,
        max_budget: float = None,
        log_utterances: UtteranceLog = None,
    ):
        """Init the class.

        Args:
            destination (str, optional): city to go to. Defaults to None.
            origin (str, optional): city of departure. Defaults to None.
            departure_date (str, optional): date of departure. Defaults to None.
            return_date (str, optional): date to return home. Defaults to None.
            max_budget (float, optional): budget at max. Defaults to None.
        """
        self.destination = destination
        self.origin = origin
        self.departure_date = departure_date
        self.return_date = return_date
        self.max_budget = max_budget
        self.log_utterances = UtteranceLog()
        self.save_next_utterance : bool = True

    def merge(self, value: object, replace_when_exist: bool = False) -> None:
        """Merge current value with another."""
        if (self.destination is None) or (replace_when_exist and value.destination is not None):
            self.destination = value.destination
        if (self.origin is None) or (replace_when_exist and value.origin is not None):
            self.origin = value.origin
        if (self.departure_date is None) or (replace_when_exist and value.departure_date is not None):
            self.departure_date = value.departure_date
        if (self.return_date is None) or (replace_when_exist and value.return_date is not None):
            self.return_date = value.return_date
        if (self.max_budget is None) or (replace_when_exist and value.max_budget is not None):
            self.max_budget = value.max_budget
