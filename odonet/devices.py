"""
Devices
"""
class Device:
    """A the base device object"""
    def __init__(self):
        pass

    def tick(self):
        return TickResult()


class TickResult:
    """An object to store the results of a device tick"""
    def __init__(self):
        self.image = None
        self.event = None
