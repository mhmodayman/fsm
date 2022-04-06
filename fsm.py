"""
In this module we implement a declarative finite state machine using method decorators.
"""


class FiniteStateMachineError(Exception):
    """
    A finite state machine exception.
    """

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class Action(object):
    """
    The Action decorator adds metadata to methods so they can be used by the finite
    state machine as actions that are executed upon entering or exiting a state.

    Arguments: state    - The state upon which the action will be executed.
               on_entry - If True the action is executed when entering the state.
               on_exit  - If True the action is executed when exiting the state.
    """

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def __call__(self, function):
        # Append metadata to the function that is necessary
        # to build a transition lookup table by the finite
        # state machine.
        state = self.kwargs.get('state')
        if not state or not isinstance(state, str) or len(state) == 0:
            raise FiniteStateMachineError('Please specify a valid action state attribute.\n Possible values are strings.')
        else:
            function.__fsm_action_state__ = state
        if 'on_entry' in self.kwargs:
            on_entry = self.kwargs.get('on_entry')
            if isinstance(on_entry, bool):
                function.__fsm_action_on_entry__ = on_entry
            else:
                raise TypeError('Please specify a valid action on_entry attribute.\n Possible values are True or False.')
        else:
            function.__fsm_action_on_entry__ = True
        if 'on_exit' in self.kwargs:
            on_exit = self.kwargs.get('on_exit')
            if isinstance(on_exit, bool):
                function.__fsm_action_on_exit__ = on_exit
            else:
                raise TypeError('Please specify a valid action on_exit attribute.\n Possible values are True or False.')
        else:
            function.__fsm_action_on_exit__ = False
        function.__fsm_action__ = True
        return function


class Guard(object):
    """
    The Guard decorator adds metadata to predicate methods so they can be used by
    the finite state machine as guards protecting transitions into states.

    Arguments: state - The state upon which the guard will be executed.
    """

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def __call__(self, function):
        # Append metadata to the function that is necessary
        # to build a transition lookup table by the finite
        # state machine.
        state = self.kwargs.get('state')
        if not state or not isinstance(state, str) or len(state) == 0:
            raise TypeError('Please specify a valid guard state attribute.\n Possible values are strings.')
        else:
            function.__fsm_guard_state__ = state
        function.__fsm_guard__ = True
        return function


class FiniteStateMachine(object):
    """
    A finite state machine.
    """

    def __init__(self, *args, **kwargs):
        super(FiniteStateMachine, self).__init__(*args, **kwargs)
        self.__fsm_transition_table__ = self.__create_lookup_table__()
        self.__state__ = self.initial_state

    def __create_lookup_table__(self):
        """
        Creates a transition lookup table based on the possible transitions.
        """
        actions = self.__get_actions__()
        guards = self.__get_guards__()
        states = self.__get_states__()
        state_map = self.__create_state_map__(actions, guards, states)
        # Create the lookup table.
        lookup_table = dict()
        for begin, end in self.transitions:
            transitions = lookup_table.get(begin)
            if not transitions:
                transitions = dict()
                lookup_table.update({begin: transitions})
            transition = transitions.get(end)
            if not transition:
                transition = dict()
                transitions.update({end: transition})
            if 'beginning_state' not in transition:
                transition.update({'beginning_state': state_map.get(begin)})
            if 'end_state' not in transition:
                transition.update({'end_state': state_map.get(end)})
        return lookup_table

    def __create_state_map__(self, actions, guards, states):
        """
        Creates a map from states to actions and guards.

        Arguments: actions - The actions declared for this finite state machine.
                   guards  - The guards declared for this finite state machine.
                   state   - The possible states for this finite state machine.
        """
        state_map = dict()
        # Make sure every state has an entry.
        for state in states:
            state_map.update({state: dict()})
        # Attach actions to their states.
        for action in actions:
            state_name = action.__fsm_action_state__
            if state_name not in states:
                raise FiniteStateMachineError('A state named %s is not declared \
                                              in the transitions list.\n Please add %s to the list of possible \
                                              transitions or modify the @Action decorator on %s.' % (state_name,
                                              state_name, action.__name__))
            state = state_map.get(state_name)
            on_entry = action.__fsm_action_on_entry__
            if 'on_entry' not in state:
                if on_entry:
                    state.update({'on_entry': action})
            elif ('on_entry' in state) and on_entry:
                raise FiniteStateMachineError('The %s state can only have one action declared for on_entry.' % state_name)
            on_exit = action.__fsm_action_on_exit__
            if 'on_exit' not in state:
                if on_exit:
                    state.update({'on_exit': action})
            elif ('on_exit' in state) and on_exit:
                raise FiniteStateMachineError('The %s state can only have one action declared for on_exit.' % state_name)
        # Attach guards to their states.
        for guard in guards:
            state_name = guard.__fsm_guard_state__
            if state_name not in states:
                raise FiniteStateMachineError('A state named %s is not declared \
                                              in the transitions list.\n Please add %s to the list of possible \
                                              transitions or modify the @Guard decorator on %s.' % (state_name,
                                              state_name, guard.__name__))
            state = state_map.get(state_name)
            if 'guard' not in state:
                state.update({'guard': guard})
            else:
                raise FiniteStateMachineError('The %s state can only have one guard declared' % state_name)
        return state_map

    def __get_actions__(self):
        """
        Returns: All the actions declared for this finite state machine.
        """
        return filter(
            lambda Callable: hasattr(Callable, '__fsm_action__'),
            self.__get_callables__()
        )

    def __get_callables__(self):
        """
        Returns: All the methods for this object.
        """
        actions = list()
        results = dir(self)
        for result in results:
            attr = getattr(self, result)
            if hasattr(attr, '__call__'):
                actions.append(attr)
        return actions

    def __get_guards__(self):
        """
        Returns: All the guards declared for this finite state machine.
        """
        return filter(lambda Callable: hasattr(Callable, '__fsm_guard__'), self.__get_callables__())

    def __get_states__(self):
        """
        Returns: The possible states based on the declared transitions.
        """
        # Make sure the user declared a set of possible transitions.
        if not self.transitions:
            raise FiniteStateMachineError('Please specify a list of possible \
                                          transitions.\n Each entry in the list is a two-tuple where the \
                                          first value is the beginning state and the second value is the \
                                          end state.')
        states = list()
        for begin, end in self.transitions:
            if begin not in states:
                states.append(begin)
            if end not in states:
                states.append(end)
        return states

    def state(self):
        return self.__state__

    def transition(self, to=None, triggered_event_description=None, transition_tailored_arguments=None):
        """
        Transitions the finite state machine to a new state.

        Arguments: to - The desired end state.
                   event - The event that caused the state change.
        """
        # Make sure we are in a good state.
        transitions = self.__fsm_transition_table__.get(self.__state__)
        if not transitions:
            raise FiniteStateMachineError('The %s state is invalid, or we have entered a terminal state.' % self.__state__)
        # Try to find the desired transition.
        transition = transitions.get(to)
        if not transition:
            raise FiniteStateMachineError('The transition from %s to %s is invalid.' % (self.__state__, to))
        # If there are any guards lets execute those now.
        if 'guard' in transition.get('end_state'):
            allowed = transition.get('end_state').get('guard')(transition_tailored_arguments)
            if not isinstance(allowed, bool):
                raise FiniteStateMachineError('A guard must only return True or False values.')
            if not allowed:
                raise FiniteStateMachineError('A guard declined the transition from %s to %s.' % (self.__state__, to))
        # Try to execute the action associated with leaving the current state.
        if 'on_exit' in transition.get('beginning_state'):
            transition.get('beginning_state').get('on_exit')(triggered_event_description, transition_tailored_arguments)
        # Try to execute the action associated with entering the new state.
        if 'on_entry' in transition.get('end_state'):
            transition.get('end_state').get('on_entry')(triggered_event_description, transition_tailored_arguments)
        # Enter the new state and we're done.
        self.__state__ = to
