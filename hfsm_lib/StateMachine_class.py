from BACKEND_INFRASTRUCTURE.NonDeterministicStateMachine_class import *
from BACKEND_INFRASTRUCTURE.NonBlockingTimer_class import NonBlockingTimer
from BACKEND_INFRASTRUCTURE.EventReactor_class import EventReactor
from BACKEND_INFRASTRUCTURE.SerialComm_class import SerialComm


class RXStateMachine(StateMachine):
    __singleton = None
    __initialized = None

    def __new__(cls, name, *args, **kwargs):
        if not cls.__singleton:
            cls.__singleton = super(RXStateMachine, cls).__new__(cls, *args, **kwargs)
        return cls.__singleton

    def __init__(self, name):
        if not self.__initialized:
            self.__initialized = True
            super().__init__(name)
            self._name = name
            # Timers and timeouts
            self.BYTE_TIMEOUT_MS = 0.05  # Timeout on a byte in the middle of a transaction
            self.DATA_TIMEOUT_MS = 0.05  # Timeout on the first byte of a transaction
            self.TX_FORBIDDEN_TIMER = NonBlockingTimer(timeout=self.DATA_TIMEOUT_MS, callback=self.TX_FORBIDDEN_callback, timer_type='ONE_SHOT')
            self.RX_DATA_TIMER = NonBlockingTimer(timeout=self.DATA_TIMEOUT_MS, callback=self.RX_DATA_timeout_callback, timer_type='ONE_SHOT')
            self.RX_BYTE_TIMER = NonBlockingTimer(timeout=self.DATA_TIMEOUT_MS, callback=self.RX_BYTE_timeout_callback, timer_type='ONE_SHOT')
            # States
            self.IDLE = State('IDLE')
            self.WAIT_RXACK_CMD = State('WAIT_RXACK_CMD')  # WAIT FOR ACK ON THE SENT CMD
            self.WAIT_RXRSP = State('WAIT_RXRSP')  # WAIT FOR RSP
            self.RXRSP = State('RXRSP')  # RECEIVING RSP
            # Events
            self.RX_BYTE = Event('RX_BYTE')  # Received a byte from serial port
            self.BYTE_TIMEOUT = Event('BYTE_TIMEOUT')
            self.DATA_TIMEOUT = Event('DATA_TIMEOUT')
            self.RX_GQ_CMD = Event('RX_GQ_CMD')  # Received a cmd on GuiQueue sent by the user
            # Design the state machine
            self.construct_SM()
            # Register callbacks in Event reactor
            self.register_cbs_in_event_reactor_map()

    def begin(self):
        print('begin')
        SerialComm()
        self.start(None)  # Start the state machine with its initial state IDLE
        EventReactor().run_event_reactor_loop()

    def process_RX_incoming_msg(self):  # receive
        print('parse_serial_incoming_msg')
        SerialComm().read_bytes(1)
        self.trigger_event(self.RX_BYTE)

    def process_GQ_incoming_msg(self):  # send
        print('process_gui_incoming_msg')
        self.trigger_event(self.RX_GQ_CMD)

    def register_cbs_in_event_reactor_map(self):
        EventReactor().register_reaction_to_reactor_map(EventReactor().GQ_event, self.process_GQ_incoming_msg)
        EventReactor().register_reaction_to_reactor_map(EventReactor().RX_event, self.process_RX_incoming_msg)

    def TX_FORBIDDEN_callback(self):
        pass

    def RX_DATA_timeout_callback(self):
        pass

    def RX_BYTE_timeout_callback(self):
        pass

    def construct_SM(self):
        self.add_states()
        self.add_events()
        self.add_entry_exit_actions()
        self.add_transitions()

    def add_states(self):
        self.add_state(self.IDLE, initial_state=True)
        self.add_state(self.WAIT_RXACK_CMD)
        self.add_state(self.WAIT_RXRSP)
        self.add_state(self.RXRSP)

    def add_events(self):
        self.add_event(self.RX_BYTE)
        self.add_event(self.BYTE_TIMEOUT)
        self.add_event(self.DATA_TIMEOUT)
        self.add_event(self.RX_GQ_CMD)

    def add_entry_exit_actions(self):
        pass

    def add_transitions(self):
        # 08. Data timeout before receiving any response yet
        T08 = self.add_transition(self.WAIT_RXRSP, self.IDLE, self.DATA_TIMEOUT)
        T08.add_condition(lambda _: True)

        # 09. Byte timeout after receiving some bytes but already in RXRSP
        T09 = self.add_transition(self.RXRSP, self.IDLE, self.BYTE_TIMEOUT)
        T09.add_condition(lambda _: True)

        # 11. Data timeout while waiting for ack on the sent CMD
        T11 = self.add_transition(self.WAIT_RXACK_CMD, self.IDLE, self.DATA_TIMEOUT)
        T11.add_condition(lambda _: True)

        # 13. received first byte while in WAIT_RXRSP (matches the in progress header ID)
        T13 = self.add_transition(self.WAIT_RXRSP, self.RXRSP, self.RX_BYTE)
        T13.add_condition(lambda _: True)

        # 14. received first byte while in WAIT_RXRSP (does not match the in progress header ID)
        T14 = self.add_transition(self.WAIT_RXRSP, self.IDLE, self.RX_BYTE)
        T14.add_condition(lambda _: True)

        # 14'. ongoing reception of a response
        T14S = self.add_transition(self.RXRSP, self.RXRSP, self.RX_BYTE)
        T14S.add_condition(lambda _: True)

        # 15. full reception of a response (good header, length)
        T15 = self.add_transition(self.RXRSP, self.RXRSP, self.RX_BYTE)
        T15.add_condition(lambda _: True)

        # 16. full reception of a response (bad header)
        T16 = self.add_transition(self.RXRSP, self.IDLE, self.RX_BYTE)
        T16.add_condition(lambda _: True)

        # 17. full reception of a response (good CRC)
        T17 = self.add_transition(self.RXRSP, self.IDLE, self.RX_BYTE)
        T17.add_condition(lambda _: True)

        # 18. full reception of a response (bad CRC)
        T18 = self.add_transition(self.RXRSP, self.IDLE, self.RX_BYTE)
        T18.add_condition(lambda _: True)

        # 19. full reception of a response (length does not match length in the sent CMD)
        T19 = self.add_transition(self.RXRSP, self.IDLE, self.RX_BYTE)
        T19.add_condition(lambda _: True)

        # 20. Received a cmd on GuiQueue sent by the user while in IDLE (transition from IDLE to wait CMD ACK
        T20 = self.add_transition(self.IDLE, self.WAIT_RXACK_CMD, self.RX_GQ_CMD)
        T20.add_condition(lambda _: True)

        # 23. transition from CMD ACK to wait RSP (a response is expected, NMI > 0)
        T23 = self.add_transition(self.WAIT_RXACK_CMD, self.WAIT_RXRSP, self.RX_BYTE)
        T23.add_condition(lambda _: True)

        # 24. transition from CMD ACK to IDLE (no response is expected, NMI = 0)
        T24 = self.add_transition(self.WAIT_RXACK_CMD, self.IDLE, self.RX_BYTE)
        T24.add_condition(lambda _: True)

        # 25. transition from CMD NACK to IDLE (regardless of afterwards response, NMI >= 0)
        T25 = self.add_transition(self.WAIT_RXACK_CMD, self.IDLE, self.RX_BYTE)
        T25.add_condition(lambda _: True)
