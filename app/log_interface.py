import Pyro5.api

@Pyro5.api.expose
class LogInterface:
    def receive_log(self, log_line: str):
        pass

