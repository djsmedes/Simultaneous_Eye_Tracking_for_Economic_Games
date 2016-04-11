"""
@author: djs
@revision history:
    *djs 06/14 - created
    *djs 04/16 - updating documentation
"""

import socket
import threading
from sys import exit
from time import sleep
from json import loads, dumps
from socket import errno


HOST = ''
BUFFER_SIZE = 4096
PORT = 11111


class Session(object):
    """ A Session is the equivalent of one experiment.

        Each session starts with the Handler waiting to receive connections. The first computer that connects sends the
        number of players that will be participating in the game (assumes that each participant is expecting the same
        number of players).
    """

    def __init__(self):
        self.lock = threading.Lock()
        self.disconnect = threading.Event()
        self.new_message = threading.Event()
        self.players = []
        self._order = []
        self._reward_game = -1
        self._num_players = 0
        self.socket = socket.socket()
        self.socket.bind((HOST, PORT))
        self.socket.listen(0)
        print('Experiment initialized.')
        
    def run(self):
        """ First tries to connect all players, then waits for one of those players to terminate the connection.
            At that point, terminates the connections with the remaining players and ends the session.
        """
        self.connect_players()
        self.disconnect.wait()
        for plyr in self.players:
            plyr.socket.close()
            plyr.stop()
            plyr.join()
        self.socket.close()
    
    @property
    def order(self):
        return self._order

    @order.setter
    def order(self, value):
        """ Can only be set once.
        :param value: the order to apply multipliers to the participants' reward
        """
        with self.lock:
            if not self._order:
                self._order = value

    @property
    def reward_game(self):
        return self._reward_game

    @reward_game.setter
    def reward_game(self, value):
        """ Can only be set once.
        :param value: the game on which to base the participants' rewards
        """
        with self.lock:
            if self._reward_game == -1:
                self._reward_game = value

    @property
    def num_players(self):
        return self._num_players

    @num_players.setter
    def num_players(self, value):
        """ Can only be set once.
        :param value: the number of players
        """
        with self.lock:
            if self._num_players == 0:
                self._num_players = value
            elif self._num_players != value:
                # problem!
                pass

    @property
    def IDs(self):
        temp = []
        for plyr in self.players:
            temp.append(plyr.ID)
        return temp

    @property
    def IPs(self):
        temp = []
        for plyr in self.players:
            temp.append(plyr.IP)
        return temp

    @property
    def all_set_up(self):
        """ Property for clients to request.
        :return: False if there are any players who haven't gotten past the instructions and calibration, True otherwise
        """
        if len(self.players) < self.num_players:
            return False
        for plyr in self.players:
            if not plyr.is_set_up:
                return False
        return True

    @property
    def all_contributions(self):
        """ The client needs to have handling for this, we just hand over all the data we have.
        :return: a dictionary where a player's IP address maps to a list of the contributions they have made
        """
        answer_dict = {}
        for plyr in self.players:
            answer_dict[plyr.IP] = plyr.contributions
        return answer_dict

    def connect_players(self):
        """ Connects all players; the first player to connect determines order, reward_game, and num_players.
        """
        print('Awaiting connections.')
        self._connect_player()
        while self.num_players == 0:
            self.new_message.wait()
        while len(self.players) < self.num_players:
            self._connect_player()
        print('All players present and accounted for.')
    
    def _connect_player(self):
        """ Connects a single player. We pass this Session object as a parameter to each PlayerThread so that they can
            directly access data about the Session, as well as signal to end the experiment.
        """
        conn, addr = self.socket.accept()     
        self.players.append(PlayerThread(conn, addr, sess=self))
        print('{} connected.'.format(self.players[-1].IP))
        self.players[-1].start()


class PlayerThread(threading.Thread):
    """ A thread to handle communication with a single client.
    """
    def __init__(self, conn, addr, sess):
        """
        :param conn: the socket to use for the connection
        :param addr: the IP address to use
        :param sess: the parent session object
        """
        super(PlayerThread, self).__init__()
        self.socket = conn
        self.socket.setblocking(0)
        self.port = addr[1]
        self.session = sess
        
        self.IP = addr[0]
        self.ID = ''
        self.is_set_up = False
        self.contributions = []
        
        self._stop = threading.Event()
     
    def message_command(self, message_dict):
        """ Parses and executes commands received from the client.
        :param message_dict: a dictionary containing the data sent by the client
                             u'request' - the type of client command. Possible types are:
                                 u'quit'   - tells the Handler to end the Session
                                 u'set'    - set a data member; expects additional u'values' subnode
                                 u'append' - append data to a data member; expects additional u'values' subnode
                                 u'get'    - get the value of a data member; expects additional u'values' subnode
        :return: a dictionary containing data to be sent to the client
                 u'category'      - the category of message, always u'handler'
                 u'request'       - the request of message, just repats back to the client what it sent
                 u'statuscode'    - http statuscode indicating what happened
                 u'statusmessage' - optional, error message if there was one
                 u'values'        - optional, contains data values to be sent back to client for u'get' commands
        """
        reply_dict = {u'category': u'handler',
                      u'request': message_dict[u'request'],
                      u'statuscode': 200
                      }
        if message_dict[u'request'] == u'quit':
            print('Quit command recved from client.')
            self.stop()
            return None
        elif message_dict[u'request'] == u'set':
            for key, value in message_dict[u'values'].iteritems():
                if hasattr(self, key):
                    setattr(self, key, value)
                elif hasattr(self.session, key):
                    setattr(self.session, key, value)
                else:
                    reply_dict[u'statuscode'] = 404
                    reply_dict[u'statusmessage'] = 'Value "{}" does not exist.'.format(key)
        elif message_dict[u'request'] == u'append':
            for key, value in message_dict[u'values'].iteritems():
                if hasattr(self, key):
                    attr_ = getattr(self, key)
                    attr_.append(value)
                elif hasattr(self.session, key):
                    attr_ = getattr(self.session, key)
                    attr_.append(value)
                else:
                    reply_dict[u'statuscode'] = 404
                    reply_dict[u'statusmessage'] = 'Value "{}" does not exist.'.format(key)
        elif message_dict[u'request'] == u'get':
            reply_dict[u'values'] = {}
            for key in message_dict[u'values']:
                if hasattr(self, key):
                    reply_dict[u'values'][key] = getattr(self, key)
                elif hasattr(self.session, key):
                    reply_dict[u'values'][key] = getattr(self.session, key)
                else:
                    reply_dict[u'values'][key] = None
                    reply_dict[u'statuscode'] = 404
                    reply_dict[u'statusmessage'] = 'Value does not exist.'
        else:
            reply_dict[u'statuscode'] = 404
            reply_dict[u'statusmessage'] = 'Request does not exist.'.format()
        self.session.new_message.set()
        self.session.new_message.clear()
        return reply_dict
    
    def stop(self):
        self._stop.set()
        
    def run(self):
        """ Main loop that communicates with clients. Note that this will set the Session's .disconnect Event just
            before terminating.
        """
        while not self._stop.is_set():
            sleep(0.250)
            try:
                messages = self.socket.recv(BUFFER_SIZE).split('\n')
            except socket.error as error_:
                if error_[0] == errno.EWOULDBLOCK:
                    continue
                elif error_[0] == 10054 or 104:  # errno.WSAECONNRESET:
                    # NOTE: this does not always work. If there is a
                    # socket still accepting connections, it is not
                    # actually stopped.
                    # What this boils down to is that if you want to
                    # quit the experiment, you have to connect all
                    # players first.
                    print('Connection closed. Exiting...')
                    self.stop()
                    break
                else:
                    raise error_
            for message in messages:
                if message == '':
                    continue
                message_dict = loads(message)
                reply = None
                if message_dict[u'category'] == u'handler':
                    reply = self.message_command(message_dict)
                else:
                    print('Recved a message that was not handler category. '
                          'Message:\n{}'.format(message_dict))
                if reply is not None:
                    try:
                        self.socket.send('{}\n'.format(dumps(reply)))
                    except socket.error as err_:
                        if err_[0] == 32:
                            print('Connection closed. Exiting...')
                            self.stop()
                        else:
                            raise err_
        self.session.disconnect.set()


class QuitterThread(threading.Thread):
    """ Barebones thread that could be used to terminate the overall program on some condition, by letting external
        code set its stop Event.
    """
    def __init__(self):
        super(QuitterThread, self).__init__()
        self.stop = threading.Event()
         
    def run(self):
        while not self.stop.is_set():
            try:
                _ = raw_input()
            except Exception:
                print('Exiting...')
                exit(0)
        
        
quitter_thr = QuitterThread()
quitter_thr.start()

while not quitter_thr.stop.is_set():
    try:
        session = Session()
        session.run()
    except Exception as err_1:
        print('an error happened: {}'.format(err_1))
        try:
            for player in session.players:
                player.socket.close()
            session.socket.close()
        except Exception as err_2:
            print('another error happened: {}'.format(err_2))


quitter_thr.join()
