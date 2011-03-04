import multiprocessing


class Timeout(Exception):
    pass


class Future(object):
    """
    A :class:`Future` is a handle to a value which are available or will be
    available in the future.

    Typically returned by calls to actor methods or accesses to actor fields.

    To get hold of the encapsulated value, call :meth:`Future.get`.
    """

    def get(self, timeout=None):
        """
        Get the value encapsulated by the future.

        If the encapsulated value is an exception, it is raised instead of
        returned.

        If ``timeout`` is :class:`None`, as default, the method will block
        until it gets a reply, potentially forever. If ``timeout`` is an
        integer or float, the method will wait for a reply for ``timeout``
        seconds, and then raise :exc:`Timeout`.

        :param block: whether to block while waiting for a reply
        :type block: boolean

        :param timeout: seconds to wait before timeout
        :type timeout: float or :class:`None`

        :return: encapsulated value
        """
        raise NotImplementedError

    def set(self, value=None):
        """
        Set the encapsulated value.

        :param value: the encapsulated value or nothing
        :type value: any picklable object or :class:`None`
        """
        raise NotImplementedError

    def set_exception(self, exception):
        """
        Set an exception as the encapsulated value.

        :param exception: the encapsulated exception
        :type exception: exception
        """
        raise NotImplementedError


try:
    import gevent
    import gevent.event

    class GeventFuture(Future):
        """
        :class:`GeventFuture` implements :class:`Future` for use with
        :class:`pykka.actor.GeventActor`.

        It encapsulates a :class:`gevent.event.AsyncResult` object which may be
        used directly, though it will couple your code with gevent.
        """

        #: The encapsulated :class:`gevent.event.AsyncResult`
        async_result = None

        def __init__(self):
            self.async_result = gevent.event.AsyncResult()

        def get(self, timeout=None):
            try:
                return self.async_result.get(timeout=timeout)
            except gevent.Timeout as e:
                raise Timeout(e)

        def set(self, value):
            self.async_result.set(value)

        def set_exception(self, exception):
            self.async_result.set_exception(exception)

except ImportError:
    pass


class ThreadingFuture(Future):
    def __init__(self):
        self.reader, self.writer = multiprocessing.Pipe(False)

    def get(self, timeout=None):
        pass
        if not self.reader.poll(timeout):
            raise Timeout('%s seconds' % timeout)
        result = self.reader.recv()
        if isinstance(result, Exception):
            raise result
        else:
            return result

    def set(self, value):
        self.writer.send(value)

    def set_exception(self, exception):
        self.set(exception)

    # TODO Implement pickle()/unpickle()


def get_all(futures, timeout=None):
    """
    Collect all values encapsulated in the list of futures.

    If ``timeout`` is not :class:`None`, the method will wait for a reply for
    ``timeout`` seconds, and then raise :exc:`pykka.future.Timeout`.

    :param futures: futures for the results to collect
    :type futures: list of `pykka.future.Future`

    :param timeout: seconds to wait before timeout
    :type timeout: float or :class:`None`

    :returns: list of results
    """
    return [future.get(timeout=timeout) for future in futures]

def wait_all(futures, timeout=None):
    """
    Wait for all futures in the results list are available.

    This is an alias for :func:`get_all`, but with a name that is more
    describing if you do not care about the return values.
    """
    return get_all(futures, timeout)
