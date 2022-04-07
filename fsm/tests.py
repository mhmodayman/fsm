from fsm import *
from unittest import TestCase, expectedFailure


class AbstractLightBulb(FiniteStateMachine):
    # Initial state.
    initial_state = 'off'

    # Possible transitions.
    transitions = [
                    ('off', 'on'),
                    ('on', 'off'),
                    ('off', 'broken'),
                    ('on', 'broken')
    ]


class LightBulb(AbstractLightBulb):
    # Handle incoming events.
    def on_message(self, message, transition_tailored_arguments):
        if message == 'turn on':
            self.transition(to='on', triggering_event=message, transition_arguments=transition_tailored_arguments)
        elif message == 'turn off':
            self.transition(to='off', triggering_event=message, transition_arguments=transition_tailored_arguments)
        elif message == 'break':
            self.transition(to='broken', triggering_event=message, transition_arguments=transition_tailored_arguments)

    @Guard(state='on')
    def check_electricity(self, next_state_tailored_arguments):
        if hasattr(self, 'electricity'):
            return self.electricity
        return False

    @Action(state='off', on_entry=True)
    def turn_off(self, message, next_state_tailored_arguments):
        self.indicator = 'dim'

    @Action(state='on', on_entry=True)
    def turn_on(self, message, next_state_tailored_arguments):
        self.indicator = 'lit'

    @Action(state='broken', on_entry=True)
    def smash(self, message, next_state_tailored_arguments):
        self.indicator = 'broken'


class LightBulbWithMultipleGuards(AbstractLightBulb):
    @Guard(state='on')
    def check_electricity(self, next_state_tailored_arguments):
        return True

    @Guard(state='on')
    def check_socket(self, next_state_tailored_arguments):
        return True


class LightBulbWithMultipleOnEnterActions(AbstractLightBulb):
    @Action(state='on', on_entry=True)
    def turn_on(self, message, next_state_tailored_arguments):
        pass

    @Action(state='on', on_entry=True)
    def turn_on_again(self, message, next_state_tailored_arguments):
        pass


class LightBulbWithMultipleOnExitActions(AbstractLightBulb):
    @Action(state='on', on_entry=False, on_exit=True)
    def turn_on(self, message, next_state_tailored_arguments):
        pass

    @Action(state='on', on_entry=False, on_exit=True)
    def turn_on_again(self, message, next_state_tailored_arguments):
        pass


class LightBulbWithBadActionState(AbstractLightBulb):
    @Action(state='bogus', on_exit=True)
    def foobar(self, message, next_state_tailored_arguments):
        pass


class LightBulbWithBadGuardState(AbstractLightBulb):
    @Guard(state='bogus', on_exit=True)
    def foobar(self, next_state_tailored_arguments):
        pass


class LightBulbTests(TestCase):
    def test_success_scenario(self):
        light_bulb = LightBulb()
        light_bulb.electricity = True
        self.assertTrue(light_bulb.state() == 'off')
        light_bulb.on_message(message='turn on', transition_tailored_arguments={})
        self.assertTrue(light_bulb.state() == 'on')  # <-- assert new state of the lightbulb
        self.assertTrue(light_bulb.indicator == 'lit')  # <-- assert action taken to reach the new state
        light_bulb.on_message(message='turn off', transition_tailored_arguments={})
        self.assertTrue(light_bulb.state() == 'off')
        self.assertTrue(light_bulb.indicator == 'dim')

    def test_invalid_transition(self):
        light_bulb = LightBulb()
        light_bulb.electricity = True
        self.assertTrue(light_bulb.state() == 'off')
        self.assertRaises(FiniteStateMachineError, light_bulb.on_message, message='turn off', transition_arguments={})
        self.assertFalse(hasattr(light_bulb, 'indicator'))

    def test_terminal_state(self):
        light_bulb = LightBulb()
        light_bulb.electricity = True
        self.assertTrue(light_bulb.state() == 'off')
        light_bulb.on_message(message='turn on', transition_tailored_arguments={})
        self.assertTrue(light_bulb.state() == 'on')
        self.assertTrue(light_bulb.indicator == 'lit')
        light_bulb.on_message(message='turn off', transition_tailored_arguments={})
        self.assertTrue(light_bulb.state() == 'off')
        self.assertTrue(light_bulb.indicator == 'dim')
        light_bulb.on_message(message='break', transition_tailored_arguments={})
        self.assertTrue(light_bulb.state() == 'broken')
        self.assertTrue(light_bulb.indicator == 'broken')
        self.assertRaises(FiniteStateMachineError, light_bulb.on_message, message='turn on', transition_arguments={})
        self.assertTrue(light_bulb.state() == 'broken')
        self.assertTrue(light_bulb.indicator == 'broken')

    def test_guard_denial(self):
        light_bulb = LightBulb()
        self.assertTrue(light_bulb.state() == 'off')
        self.assertRaises(FiniteStateMachineError, light_bulb.on_message, message='turn on', transition_arguments={})
        self.assertTrue(light_bulb.state() == 'off')
        self.assertFalse(hasattr(light_bulb, 'indicator'))

    def test_multiple_guards(self):
        light_bulb = None
        self.assertRaises(FiniteStateMachineError, LightBulbWithMultipleGuards)
        self.assertTrue(light_bulb is None)

    def test_multiple_on_entry_actions(self):
        light_bulb = None
        self.assertRaises(FiniteStateMachineError, LightBulbWithMultipleOnEnterActions)
        self.assertTrue(light_bulb is None)

    def test_multiple_on_exit_actions(self):
        light_bulb = None
        self.assertRaises(FiniteStateMachineError, LightBulbWithMultipleOnExitActions)
        self.assertTrue(light_bulb is None)

    def test_bad_action_state(self):
        light_bulb = None
        self.assertRaises(FiniteStateMachineError, LightBulbWithBadActionState)
        self.assertTrue(light_bulb is None)

    def test_bad_guard_state(self):
        light_bulb = None
        self.assertRaises(FiniteStateMachineError, LightBulbWithBadGuardState)
        self.assertTrue(light_bulb is None)
