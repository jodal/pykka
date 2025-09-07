=======
Testing
=======

Pykka actors can be tested using the regular Python
testing tools like `pytest <https://docs.pytest.org/>`_,
:mod:`unittest`, and :mod:`unittest.mock`.

To test actors in a setting as close to production as possible,
a typical pattern is the following:

1. In the test setup,
   start an actor together with any actors/collaborators it depends on.
   The dependencies will often be replaced by mocks to control their behavior.
2. In the test,
   :meth:`~pykka.ActorRef.ask` or :meth:`~pykka.ActorRef.tell`
   the actor something.
3. In the test,
   assert on the actor's state
   or the return value from the :meth:`~pykka.ActorRef.ask`.
4. In the test teardown,
   stop the actor to properly clean up before the next test.

An example
==========

Let's look at an example actor that we want to test:

.. literalinclude:: ../examples/producer.py

We can test this actor with `pytest`_ by mocking the consumer
and asserting that it receives a newly produced item:

.. literalinclude:: ../examples/producer_test.py

If this way of setting up and tearing down test resources is unfamiliar to you,
it is strongly recommended to read up on pytest's great
`fixture <https://docs.pytest.org/en/latest/fixture.html>`_ feature.
