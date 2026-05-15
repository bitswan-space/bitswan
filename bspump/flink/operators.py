"""
Flink operator wrappers for BitSwan processors.

Maps BitSwan @step and @async_step decorators to Flink operators:
- @step (sync) -> MapFunction
- @async_step (generator) -> FlatMapFunction

Uses cloudpickle for serializing Python functions to Flink workers.
"""

from typing import Any, Callable, Tuple, Iterator

# Type alias for event-context tuples
EventContext = Tuple[bytes, dict]


class BitSwanMapFunction:
    """Flink MapFunction wrapper for @step decorated functions.

    Wraps a synchronous BitSwan processor function that transforms
    a single event into a single output event.

    The function is serialized using cloudpickle and deserialized
    on the Flink TaskManager when the job runs.
    """

    def __init__(self, func_bytes: bytes):
        """Initialize with pickled function bytes.

        Args:
            func_bytes: cloudpickle serialized function
        """
        self.func_bytes = func_bytes
        self.func: Callable[[Any], Any] = None  # type: ignore

    def open(self, runtime_context: Any) -> None:
        """Called when the operator is initialized on the TaskManager.

        Deserializes the function from bytes.
        """
        import cloudpickle

        self.func = cloudpickle.loads(self.func_bytes)

    def map(self, value: EventContext) -> EventContext:
        """Process a single event.

        Args:
            value: Tuple of (event_bytes, context_dict)

        Returns:
            Tuple of (result_bytes, context_dict) or None if filtered
        """
        event, context = value
        result = self.func(event)

        if result is None:
            # Event was filtered out
            return None  # type: ignore

        # Ensure result is bytes
        if isinstance(result, str):
            result = result.encode("utf-8")
        elif isinstance(result, dict):
            import json

            result = json.dumps(result).encode("utf-8")

        return (result, context)


class BitSwanFlatMapFunction:
    """Flink FlatMapFunction wrapper for @async_step decorated functions.

    Wraps a BitSwan generator function that can produce zero, one, or
    multiple output events from a single input event.

    The function signature is: async def func(inject, event) -> None
    where inject is a callback to emit events.

    For Flink, we convert this to a synchronous flat_map that yields
    multiple results.
    """

    def __init__(self, func_bytes: bytes):
        """Initialize with pickled function bytes.

        Args:
            func_bytes: cloudpickle serialized function
        """
        self.func_bytes = func_bytes
        self.func: Callable = None  # type: ignore

    def open(self, runtime_context: Any) -> None:
        """Called when the operator is initialized on the TaskManager.

        Deserializes the function from bytes.
        """
        import cloudpickle

        self.func = cloudpickle.loads(self.func_bytes)

    def flat_map(self, value: EventContext) -> Iterator[EventContext]:
        """Process a single event, potentially producing multiple outputs.

        Args:
            value: Tuple of (event_bytes, context_dict)

        Yields:
            Tuples of (result_bytes, context_dict)
        """
        import asyncio

        event, context = value
        results = []

        # Create an injector that collects results
        async def inject(output_event: Any) -> None:
            # Ensure output is bytes
            if isinstance(output_event, str):
                output_event = output_event.encode("utf-8")
            elif isinstance(output_event, dict):
                import json

                output_event = json.dumps(output_event).encode("utf-8")
            results.append(output_event)

        # Run the async function
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()

        loop.run_until_complete(self.func(inject, event))

        # Yield all collected results with context preserved
        for result in results:
            yield (result, context)


def create_map_function(func: Callable[[Any], Any]) -> BitSwanMapFunction:
    """Create a BitSwanMapFunction from a @step function.

    Args:
        func: The decorated step function

    Returns:
        BitSwanMapFunction ready for Flink
    """
    import cloudpickle

    func_bytes = cloudpickle.dumps(func)
    return BitSwanMapFunction(func_bytes)


def create_flat_map_function(
    func: Callable[[Callable, Any], None]
) -> BitSwanFlatMapFunction:
    """Create a BitSwanFlatMapFunction from an @async_step function.

    Args:
        func: The decorated async_step function

    Returns:
        BitSwanFlatMapFunction ready for Flink
    """
    import cloudpickle

    func_bytes = cloudpickle.dumps(func)
    return BitSwanFlatMapFunction(func_bytes)
