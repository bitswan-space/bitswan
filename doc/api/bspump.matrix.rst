bspump.matrix
=============

Matrix data structures for multi-dimensional analysis.

.. automodule:: bspump.matrix
   :members:
   :undoc-members:
   :show-inheritance:

Matrix
------

In-memory matrix for multi-dimensional data.

.. code-block:: python

    from bspump.matrix import Matrix

    # Create a 100x100 matrix
    matrix = Matrix(app, "MyMatrix", (100, 100))

    # Access elements
    matrix[10, 20] = 5
    value = matrix[10, 20]

    # Increment
    matrix[10, 20] += 1

PersistentMatrix
----------------

Matrix with disk persistence for recovery.

.. code-block:: python

    from bspump.matrix import PersistentMatrix

    matrix = PersistentMatrix(
        app, "PersistentMatrix",
        path="/data/matrix.dat",
        shape=(1000, 1000)
    )

The matrix state is automatically saved and restored on restart.

NamedMatrix
-----------

Matrix with named dimensions.

.. code-block:: python

    from bspump.matrix import NamedMatrix

    matrix = NamedMatrix(app, "NamedMatrix", (100, 100))

    # Set row/column names
    matrix.set_row_name(0, "user_001")
    matrix.set_col_name(0, "product_001")

    # Access by name
    matrix.set("user_001", "product_001", 5)
    value = matrix.get("user_001", "product_001")

PersistentNamedMatrix
---------------------

Named matrix with persistence.

.. code-block:: python

    from bspump.matrix import PersistentNamedMatrix

    matrix = PersistentNamedMatrix(
        app, "PersistentNamedMatrix",
        path="/data/named_matrix.dat",
        shape=(1000, 1000)
    )

Using in Analyzers
------------------

.. code-block:: python

    class MatrixAnalyzer(bspump.Analyzer):
        def __init__(self, app, pipeline, id=None, config=None):
            super().__init__(app, pipeline, id, config)
            self.matrix = Matrix(app, "AnalysisMatrix", (100, 100))

        def evaluate(self, context, event):
            x = event.get("x", 0) % 100
            y = event.get("y", 0) % 100
            self.matrix[x, y] += 1
            event["cell_count"] = self.matrix[x, y]
            return event

Matrix Operations
-----------------

.. code-block:: python

    # Get shape
    shape = matrix.shape

    # Reset to zeros
    matrix.zeros()

    # Sum all elements
    total = matrix.sum()

    # Get row/column
    row = matrix[10, :]
    col = matrix[:, 20]

Configuration
-------------

.. code-block:: ini

    [matrix:PersistentMatrix]
    path=/data/matrix.dat
    # Auto-save interval in seconds
    save_interval=60

Best Practices
--------------

1. **Use PersistentMatrix for recovery**: Important data survives restarts
2. **Size appropriately**: Large matrices consume memory
3. **Use NamedMatrix for clarity**: Named dimensions improve readability
4. **Periodic saves**: Configure save_interval for important data
