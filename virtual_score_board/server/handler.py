from autobahn.twisted.websocket import WebSocketServerProtocol
from twisted.internet.defer import Deferred
from twisted.internet import task, reactor
from virtual_score_board.models import Game
from virtual_score_board.command_parser import Parser, ParseError, NotLogged, WrongCredentials
from virtual_score_board.parser_types import ParserTypeError
import json

game = Game()

template_dict = {
    'home_name': 'Foo',
    'home_score': 0,
    'home_penalty': False,
    'home_timeout': False,
    'away_name': 'Bar',
    'away_score': 0,
    'away_penalty': False,
    'away_timeout': False,
    'match_seconds': 350,
    'match_period': 1
}


class ServerHandler(WebSocketServerProtocol):
    second_deffer = None
    parser = Parser(game)

    def onConnect(self, request):
        print("Client connecting: {0}".format(request.peer))


    def onOpen(self):
        print("WebSocket connection open.")
        self.send_data_for_second()

    def onMessage(self, payload, isBinary):
        if isBinary:
            print("Binary message received: {0} bytes".format(len(payload)))
        else:
            print("Text message received: {0}".format(payload.decode('utf8')))
            message = payload.decode('utf8')
            try:
                data = json.loads(message)
            except ValueError:
                state = json.dumps({"Error": "This is not a json"})
                self.sendMessage(state.encode('utf-8'), isBinary=False)
                return
            try:
                self.parser.parse_and_execute(data)
            except (ParseError, ParserTypeError, NotLogged, WrongCredentials)  as e:
                state = json.dumps({"Error": str(e)})
                self.sendMessage(state.encode('utf-8'), isBinary=False)
            except:
                state = json.dumps({"Error": "Unknown Error"})
                self.sendMessage(state.encode('utf-8'), isBinary=False)

    def onClose(self, wasClean, code, reason):
        if self.second_deffer is not None:
            self.second_deffer.cancel()
        print("WebSocket connection closed: {0}".format(reason))

    def send_data(self):
        dictionary = game.to_dict()
        dictionary["logged"] = self.parser.is_logged()
        state = json.dumps(dictionary)
        self.sendMessage(state.encode('utf-8'), isBinary=False)

    def send_data_for_second(self):
        self.send_data()
        self.second_deffer = task.deferLater(reactor, 1.0, self.send_data_for_second)