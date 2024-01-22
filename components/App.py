import asyncio


class BaseApp:
    """
    Defines the basic functionality of an app. All apps should inherit from this class.

    :param app_name: The name of the app.
    :param logger: An instance of the logger class.
    :param status_led: An instance of the status LED class.
    """

    def __init__(
        self,
        app_name: str = "BaseApp",
        drivers: list = [],
        modules: list = [],
    ):
        """
        Initialize the app.

        :param app_name: The name of the app.
        :param drivers: A list of tuples containing the driver path to import, the name of the driver, and the arguments to pass to the driver.
        :param modules: A list of tuples containing the module path to import, the name of the module, and the arguments to pass to the module.

        """

        # Initialize app name
        self._app_name = app_name

    def __repr__(self) -> str:
        return self._app_name

    def __str__(self) -> str:
        return self._app_name

    def load_module(self, module_path, module_name, module_args=[], module_kwargs={}):
        """
        Import and load a module.

        :param module_path: The path to the module to import.
        :param module_name: The name of the module to import. (Will also become the attribute name)
        :param module_args: The arguments to pass to the module.
        :param module_kwargs: The keyword arguments to pass to the module.

        :return: None

        Example (loads the TaskStore module and creates an instance of it as attribute "TaskStore"):
        self.load_module("components.TaskStore", "TaskStore")
        self.load_module("components.TaskStore", "TaskStore", ["arg1", "arg2"], {"kwarg1": "kwarg1", "kwarg2": "kwarg2"})
        """

        # Import module
        module_module = __import__(module_path, None, None, [module_name])
        module_class = getattr(module_module, module_name)

        # Initialize module
        module_instance = module_class(self, *module_args, **module_kwargs)

        # Store module instance
        setattr(self, module_name, module_instance)

    async def _loop(self, infinite: bool = True):
        """
        Main loop.

        :param infinite: Whether or not to run the loop infinitely.
        """

        # Run the loop infinitely
        if infinite:
            while True:
                await asyncio.sleep(0)

        # Run the loop once
        else:
            await asyncio.sleep(0)
