from multiprocessing.reduction import reduce_connection
import pickle


def pickle_connection(connection):
    """Pickles a connection object"""
    return pickle.dumps(reduce_connection(connection))


def unpickle_connection(pickled_connection):
    """Unpickles a connection object"""
    # From http://stackoverflow.com/questions/1446004
    (func, args) = pickle.loads(pickled_connection)
    return func(*args)
