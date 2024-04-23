from utils.data_structures import Stack


class NegotiationEvent:
    def __init__(self):
        self.initiator = None  # Who proposed term changes
        self.proposal_datetime = None  # When the changes were proposed
        self.effect_datetime = None  # When the changes went into effect
        self.changes = None  # Text description of changes made

    def set_initiator(self, initiator):
        self.initiator = initiator

    def get_initiator(self):
        return self.initiator

    # Use UTC for a global standard
    def set_proposal_datetime(self, datetime):
        self.proposal_datetime = datetime

    def get_proposal_datetime(self):
        return self.proposal_datetime

    # Use UTC for a global standard
    def set_effect_datetime(self, datetime):
        self.effect_datetime = datetime

    def get_effect_datetime(self):
        return self.effect_datetime

    def set_changes(self, changes):
        self.changes = changes

    def get_changes(self):
        return self.changes

    def __str__(self):
        return (f"The following changes were initiated by {self.initiator} on {self.proposal_datetime} and"
                f"accepted on {self.effect_datetime}: \n\n{self.changes}")


class NegotiationHistory:
    def __init__(self):
        self.stack = Stack()

    def add_negotiation_event(self, negotiation_event: NegotiationEvent):
        self.stack.push(negotiation_event)

    def remove_last_negotiation_event(self):
        self.stack.pop()

    # We used two stacks to get the events in proper chronological order
    # before returning them in a list
    def get_all_negotiation_events(self):
        events = []
        stack = self.stack  # Make sure this doesn't empty the original stack, in the unit test cases
        rev_stack = Stack()

        while not stack.is_empty():
            rev_stack.push(stack.pop().value)

        while not rev_stack.is_empty():
            events.append(rev_stack.pop().value)

        return events
