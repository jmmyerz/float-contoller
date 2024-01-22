import asyncio


class TaskStore:
    """
    Stores the awaitable references to tasks to allow for cancellation and deletion.

    To be used within the app class.
    """

    def __init__(self, context):
        self._context = context
        self._taskstore = {}

    @property
    def ts(self) -> dict:
        """
        Get the taskstore dictionary for printing to the REPL.
        This should be used for debugging purposes only.

        :return: The taskstore dictionary.
        """
        return self._taskstore

    def create_task(
        self,
        coro,
        name: str,
        module: str = None,
        recreate=False,
        coro_args=None,
        coro_kwargs=None,
    ) -> True or Exception:
        """
        Schedule a coroutine to be executed and store a reference to it in the taskstore.

        :param coro: The coroutine to create.
        :param name: The name of the task to create.
        :param recreate: Whether or not to recreate the task if it already exists.

        :param coro_args: The arguments to pass to the coroutine.
        :param coro_kwargs: The keyword arguments to pass to the coroutine.

        :return: True if the task was created, otherwise an exception.
        """

        name = name if name != None else coro.__name__

        if module != None:
            if module not in self._taskstore:
                self._taskstore[module] = {}

        ts = self._taskstore[module] if module != None else self._taskstore

        try:
            if name in ts:
                if recreate:
                    ts[name].cancel()
                else:
                    return RuntimeWarning(
                        "Task " + name + " already exists, recreate was not set"
                    )

            ts[name] = asyncio.create_task(coro(*coro_args, **coro_kwargs))

            return True

        except Exception as e:
            print("Failed to create task: " + str(e))
            return e

    def retrieve_task(self, name: str, module: str = None) -> asyncio.Task or None:
        """
        Retrieve a task from the taskstore.

        :param name: The name of the task to retrieve.
        :param moduke: Optional module name to retrieve task from.
        :return: The task if it exists, None otherwise.
        """
        try:
            return (
                self._taskstore[name]
                if module == None
                else self._taskstore[module][name]
            )
        except:
            return None

    def retrieve_all_tasks(self) -> list or None:
        """
        Retrieve all tasks from the taskstore.
        If the value of an item is a dictionary, then recurse into that dictionary to return its tasks.

        :return: A list of all task names in the taskstore.
        """
        try:
            l = []
            for task in self._taskstore:
                if isinstance(self._taskstore[task], dict):
                    l += self.retrieve_all_tasks(self._taskstore[task])
                else:
                    l.append(task)
            return l
        except:
            return None

    def retrieve_all_module_tasks(self, module: str) -> list or None:
        """
        Retrieve all tasks from the taskstore for a given module.

        :return: A list of all task names in the taskstore for a given module.
        """
        try:
            return self._taskstore[module].keys()
        except:
            return None

    def cancel_task(self, name: str, module: str = None) -> bool:
        """
        Cancel a task.

        :param name: The name of the task to cancel.
        :param moduke: Optional module name to cancel task from.
        :return: True if the task was cancelled, False otherwise.
        """
        try:
            self._taskstore[name].cancel() if module == None else self._taskstore[
                module
            ][name].cancel()
            return True
        except:
            return False

    def cancel_all_tasks(self) -> bool:
        """
        Cancel all tasks.
        If the value of an item is a dictionary, then recurse into that dictionary to cancel its tasks.

        :return: True if the tasks were cancelled, False otherwise.
        """
        try:
            for task in self._taskstore:
                if isinstance(self._taskstore[task], dict):
                    self.cancel_all_tasks(self._taskstore[task])
                else:
                    self._taskstore[task].cancel()
            return True
        except:
            return False

    def delete_task(self, name: str, module: str = None) -> bool:
        """
        Delete a task. Will cancel the task if it is running.

        :param name: The name of the task to delete.
        :param moduke: Optional module name to delete task from.
        :return: True if the task was deleted, False otherwise.
        """
        try:
            self.cancel_task(name, module)
            ts = self._taskstore[module] if module != None else self._taskstore
            del ts[name]
            return True
        except:
            return False

    def delete_all_tasks(self) -> bool:
        """
        Delete all tasks. Will cancel the tasks if they are running.
        If the value of an item is a dictionary, then recurse into that dictionary to delete its tasks.

        :return: True if the tasks were deleted, False otherwise.
        """
        try:
            for task in self._taskstore:
                if isinstance(self._taskstore[task], dict):
                    self.delete_all_tasks(self._taskstore[task])
                else:
                    self.cancel_task(task)
                    del self._taskstore[task]
            return True
        except:
            return False
