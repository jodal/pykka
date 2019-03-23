def await_dunder_future(self):
    yield
    value = self.get()
    return value


async def await_keyword(val):
    return await val
