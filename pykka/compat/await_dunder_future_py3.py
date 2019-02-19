def await_dunder_future(self):
    yield
    value = self.get()
    return value
