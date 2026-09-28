class ArduinoWeightAdapter:
    def __init__(self, parser):
        self.parser=parser

    def read(self, message):
        return self.parser(message)
