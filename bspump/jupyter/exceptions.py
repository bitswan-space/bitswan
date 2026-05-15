"""
Exceptions for controlling event flow in Jupyter notebooks.

These exceptions provide a clean way to control event processing flow
without using conditional logic throughout your notebook cells.
"""


class SkipEvent(Exception):
    """
    Raise this exception to drop the current event without processing it further.

    The event will not be sent to the sink. This is useful for filtering
    events early in the processing pipeline.

    Example:
        if event.get("type") == "spam":
            raise SkipEvent()

        # This code only runs for non-spam events
        event["processed"] = True
    """
    pass


class FinalizeEvent(Exception):
    """
    Raise this exception to send an event to the sink immediately,
    skipping any remaining processing cells.

    This is useful for early exit scenarios where you want to output
    a result without running through all processing steps.

    Example:
        if event.get("cached"):
            # Send cached result directly to sink
            raise FinalizeEvent(event)

        # This code only runs for non-cached events
        event["result"] = expensive_computation(event)

    Args:
        event: The event to send to the sink
    """

    def __init__(self, event):
        self.event = event
        super().__init__()
