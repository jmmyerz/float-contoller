class BaseDriver:
    def __init__(self, context: object = None):
        self._context = context  # This is the app or module that owns the driver

    @property
    def context(self) -> object:
        return self._context

    # Set __name__ to the class name of this driver
    @property
    def __name__(self) -> str:
        return self.__class__.__name__

    def get_wrapped_function(self, funcname: str) -> callable:
        """
        Get a wrapped function.
        Used for creating asyncio tasks within the correct context.

        :param funcname: The name of the function to wrap.
        :return: The wrapped function.
        """
        wrapped_self = getattr(self._context, self.__name__)
        wrapped_func = getattr(wrapped_self, funcname)
        return wrapped_func
