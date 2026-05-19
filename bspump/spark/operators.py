"""
Spark UDF wrappers for BitSwan processors.

Maps BitSwan @step and @async_step decorators to Spark UDFs:
- @step (sync) -> UDF returning StringType, used with withColumn
- @async_step (generator) -> UDF returning ArrayType, used with explode

Uses cloudpickle for serializing Python functions to Spark executors.
"""

import json
from typing import Any, Callable, List


def create_map_udf(func: Callable[[Any], Any]):
    """Create a Spark UDF from a @step function.

    The UDF processes a single event string and returns a transformed string.
    Returns None if the function filters out the event.

    Args:
        func: The decorated step function

    Returns:
        A PySpark UDF ready for use with withColumn
    """
    import cloudpickle
    from pyspark.sql.functions import udf
    from pyspark.sql.types import StringType

    func_bytes = cloudpickle.dumps(func)

    @udf(returnType=StringType())
    def wrapper(event_str: str) -> str:
        import cloudpickle as cp

        f = cp.loads(func_bytes)

        # Handle input - could be string or bytes
        if isinstance(event_str, str):
            event = event_str.encode("utf-8")
        else:
            event = event_str

        # Call the function
        result = f(event)

        if result is None:
            return None

        # Handle output - ensure string for Spark
        if isinstance(result, bytes):
            return result.decode("utf-8")
        elif isinstance(result, dict):
            return json.dumps(result)
        elif isinstance(result, str):
            return result
        else:
            return str(result)

    return wrapper


def create_flatmap_udf(func: Callable[[Callable, Any], None]):
    """Create a Spark UDF from an @async_step function.

    The UDF processes a single event and returns an array of output events.
    This is used with explode() to produce multiple output rows.

    Args:
        func: The decorated async_step function with signature (inject, event) -> None

    Returns:
        A PySpark UDF returning ArrayType(StringType()) for use with explode
    """
    import cloudpickle
    from pyspark.sql.functions import udf
    from pyspark.sql.types import ArrayType, StringType

    func_bytes = cloudpickle.dumps(func)

    @udf(returnType=ArrayType(StringType()))
    def wrapper(event_str: str) -> List[str]:
        import asyncio
        import cloudpickle as cp

        f = cp.loads(func_bytes)
        results = []

        # Handle input
        if isinstance(event_str, str):
            event = event_str.encode("utf-8")
        else:
            event = event_str

        # Create an injector that collects results
        async def inject(output_event: Any) -> None:
            if isinstance(output_event, bytes):
                results.append(output_event.decode("utf-8"))
            elif isinstance(output_event, dict):
                results.append(json.dumps(output_event))
            elif isinstance(output_event, str):
                results.append(output_event)
            else:
                results.append(str(output_event))

        # Run the async function
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()

        loop.run_until_complete(f(inject, event))

        return results

    return wrapper


# Standalone versions for testing without Spark context
class BitSwanMapFunction:
    """Standalone wrapper for testing @step functions without Spark.

    This mirrors the Flink BitSwanMapFunction interface for testing.
    """

    def __init__(self, func_bytes: bytes):
        """Initialize with pickled function bytes.

        Args:
            func_bytes: cloudpickle serialized function
        """
        self.func_bytes = func_bytes
        self.func: Callable[[Any], Any] = None  # type: ignore

    def open(self, runtime_context: Any) -> None:
        """Called to initialize the function.

        Deserializes the function from bytes.
        """
        import cloudpickle

        self.func = cloudpickle.loads(self.func_bytes)

    def map(self, value: str) -> str:
        """Process a single event.

        Args:
            value: Event string

        Returns:
            Transformed event string or None if filtered
        """
        # Handle input
        if isinstance(value, str):
            event = value.encode("utf-8")
        else:
            event = value

        result = self.func(event)

        if result is None:
            return None

        # Handle output
        if isinstance(result, bytes):
            return result.decode("utf-8")
        elif isinstance(result, dict):
            return json.dumps(result)
        elif isinstance(result, str):
            return result
        else:
            return str(result)


class BitSwanFlatMapFunction:
    """Standalone wrapper for testing @async_step functions without Spark.

    This mirrors the Flink BitSwanFlatMapFunction interface for testing.
    """

    def __init__(self, func_bytes: bytes):
        """Initialize with pickled function bytes.

        Args:
            func_bytes: cloudpickle serialized function
        """
        self.func_bytes = func_bytes
        self.func: Callable = None  # type: ignore

    def open(self, runtime_context: Any) -> None:
        """Called to initialize the function.

        Deserializes the function from bytes.
        """
        import cloudpickle

        self.func = cloudpickle.loads(self.func_bytes)

    def flat_map(self, value: str) -> List[str]:
        """Process a single event, producing multiple outputs.

        Args:
            value: Event string

        Returns:
            List of output event strings
        """
        import asyncio

        # Handle input
        if isinstance(value, str):
            event = value.encode("utf-8")
        else:
            event = value

        results = []

        # Create an injector that collects results
        async def inject(output_event: Any) -> None:
            if isinstance(output_event, bytes):
                results.append(output_event.decode("utf-8"))
            elif isinstance(output_event, dict):
                results.append(json.dumps(output_event))
            elif isinstance(output_event, str):
                results.append(output_event)
            else:
                results.append(str(output_event))

        # Run the async function
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()

        loop.run_until_complete(self.func(inject, event))

        return results
