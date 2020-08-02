from lib.logger import Logger


class Visualizer(object):
    def __init__(
        self,
        logger: Logger
    ):
        super().__init__()

        self.__logger__ = logger

    def get_name(
        self
    ) -> str:
        """
        Get the name of the visualizer.

        Returns:
            str: The name of the visualizer.
        """
        return self.__class__.__name__

    def update(
        self,
        renderer,
        time_slice: float
    ):
        pass
