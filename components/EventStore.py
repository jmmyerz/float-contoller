import asyncio


class EventStore:
    """
    This class implements an event store.

    It is used to store events and tasks subscribed to them.
    """

    def __init__(self):
        """
        Initialize the eventstore dictionary
        """
        self._eventstore = {}
        self._app = None

    @property
    def app(self) -> object:
        """
        Get the parent app or module.

        :return: The parent app or module.
        """
        return self._app

    @app.setter
    def app(self, app: object):
        """
        Set the parent app or module.

        :param app: The parent app or module.
        """
        self._app = app

    def create_event(self, module: str | object, name: str) -> bool:
        """
        Create an event and store it in the eventstore along with a list of tasks subscribed to it.

        :param name: The name of the event.
        :return: True if the event was created, False otherwise.
        """
        module = module if isinstance(module, str) else module.__name__

        try:
            if module not in self._eventstore:
                self._eventstore[module] = {}

            if name in self._eventstore[module]:
                return False

            self._eventstore[module][name] = (asyncio.Event(), [])
            return True

        except Exception as e:
            return False

    def retrieve_event(self, module: str | object, name: str) -> asyncio.Event:
        """
        Retrieve an event from the eventstore.

        :param name: The name of the event to retrieve.
        :return: The event if it exists, None otherwise.
        """
        module = module if isinstance(module, str) else module.__name__

        try:
            return self._eventstore[module][name][0]
        except:
            return None

    def retrieve_all_module_events(self, module: str | object) -> list:
        """
        Retrieve all of a module's events from the eventstore.

        :param module: The module to retrieve events for.
        :return: A list of all events in the eventstore.
        """
        module = module if isinstance(module, str) else module.__name__

        try:
            return self._eventstore[module].keys()
        except:
            return None

    def retrieve_all_events(self) -> list:
        """
        Retrieve all events from the eventstore.

        :return: A list of all events in the eventstore.
        """
        l = []
        try:
            for module in self._eventstore:
                for event_tuple in self._eventstore[module]:
                    l.apppend(event_tuple)
            return l
        except:
            return None

    def set_event(self, module: str | object, name: str) -> bool:
        """
        Set an event.

        :param name: The name of the event to set.
        :return: True if the event was set, False otherwise.
        """
        module = module if isinstance(module, str) else module.__name__

        try:
            self._eventstore[name][0].set()
            return True
        except:
            return False

    def clear_event(self, module: str | object, name: str) -> bool:
        """
        Clear an event.

        :param name: The name of the event to clear.
        :return True if the event was cleared, False otherwise.
        """
        module = module if isinstance(module, str) else module.__name__

        try:
            self._eventstore[module][name][0].clear()
            return True
        except:
            return False

    def delete_event(self, module: str | object, name: str) -> bool:
        """
        Delete an event.

        :param name: The name of the event to delete.
        :return: True if the event was deleted, False otherwise.
        """
        module = module if isinstance(module, str) else module.__name__

        try:
            del self._eventstore[module][name]
            return True
        except:
            return False

    def subscribe_task(
        self, module: str | object, name: str, task: asyncio.Task
    ) -> bool:
        """
        Subscribe a task to an event.

        :param name: The name of the event to subscribe to.
        :param task: The task to subscribe.
        :return: True if the task was subscribed, False otherwise.
        """
        module = module if isinstance(module, str) else module.__name__

        try:
            self._eventstore[module][name][1].append(task)
            return True
        except:
            return False

    def unsubscribe_task(
        self, module: str | object, name: str, task: asyncio.Task
    ) -> bool:
        """
        Unsubscribe a task from an event.

        :param name: The name of the event to unsubscribe from.
        :param task: The task to unsubscribe.
        :return: True if the task was unsubscribed, False otherwise.
        """
        module = module if isinstance(module, str) else module.__name__

        try:
            self._eventstore[module][name][1].remove(task)
            return True
        except:
            return False

    def execute_subscribers(self, event: asyncio.Event) -> bool:
        """
        Execute all subscribers of an event.

        :param event: The event to execute subscribers for.
        :return: True if the subscribers were executed, False otherwise.
        """

        async def _async():
            pass

        try:
            for task in self._eventstore[event][1]:
                if isinstance(task(), _async()):
                    self.app.taskstore.create_task(task)
                else:
                    task()
            return True
        except Exception as e:
            raise e
            # return False
