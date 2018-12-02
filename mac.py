# mac.py edit from PyUserInput

import Quartz

# Taken from events.h
# /System/Library/Frameworks/Carbon.framework/Versions/A/Frameworks/HIToolbox.framework/Versions/A/Headers/Events.h
character_translate_table = {
    'a': 0x00,
    's': 0x01,
    'd': 0x02,
    'f': 0x03,
    'h': 0x04,
    'g': 0x05,
    'z': 0x06,
    'x': 0x07,
    'c': 0x08,
    'v': 0x09,
    'b': 0x0b,
    'q': 0x0c,
    'w': 0x0d,
    'e': 0x0e,
    'r': 0x0f,
    'y': 0x10,
    't': 0x11,
    '1': 0x12,
    '2': 0x13,
    '3': 0x14,
    '4': 0x15,
    '6': 0x16,
    '5': 0x17,
    '=': 0x18,
    '9': 0x19,
    '7': 0x1a,
    '-': 0x1b,
    '8': 0x1c,
    '0': 0x1d,
    ']': 0x1e,
    'o': 0x1f,
    'u': 0x20,
    '[': 0x21,
    'i': 0x22,
    'p': 0x23,
    'l': 0x25,
    'j': 0x26,
    '\'': 0x27,
    'k': 0x28,
    ';': 0x29,
    '\\': 0x2a,
    ',': 0x2b,
    '/': 0x2c,
    'n': 0x2d,
    'm': 0x2e,
    '.': 0x2f,
    '`': 0x32,
    ' ': 0x31,
    '\r': 0x24,
    '\t': 0x30,
    '\n': 0x24,
    'return' : 0x24,
    'tab' : 0x30,
    'space' : 0x31,
    'delete' : 0x33,
    'escape' : 0x35,
    'command' : 0x37,
    'shift' : 0x38,
    'capslock' : 0x39,
    'option' : 0x3A,
    'alternate' : 0x3A,
    'control' : 0x3B,
    'rightshift' : 0x3C,
    'rightoption' : 0x3D,
    'rightcontrol' : 0x3E,
    'function' : 0x3F,

    'home' : 0x73,
    'pageup' : 0x74,
    'backspace' : 0x75,
    'end' : 0x77,
    'pagedown' : 0x79,
    'f1' : 0x7a,
    'left' : 0x7b,
    'right' : 0x7c,
    'down' : 0x7d,
    'up' : 0x7e,
}

#inverse of character_translate_table for key code to name lookups
key_code_translate_table = dict((key_code, key_name) for key_name, key_code in character_translate_table.items())

class PyKeyboard(object):

    def __init__(self):
        self.modifier_table = {'Shift':False,'Command':False,'Control':False,'Alternate':False}

    def press_key(self, key):
        if key.title() in self.modifier_table:
            self.modifier_table.update({key.title():True})

        self._press_normal_key(key, True)

    def release_key(self, key):
        # remove the key
        if key.title() in self.modifier_table:
            self.modifier_table.update({key.title():False})

        self._press_normal_key(key, False)

    def _press_normal_key(self, key, down):
        try:
            key_code = character_translate_table[key.lower()]
            event = Quartz.CGEventCreateKeyboardEvent(None, key_code, down)
            flg = 0
            for mkey in self.modifier_table:
                if self.modifier_table[mkey]:
                    if mkey == 'Shift':
                        flg |= Quartz.kCGEventFlagMaskShift
                    if mkey == 'Command':
                        flg |= Quartz.kCGEventFlagMaskCommand
                    if mkey == 'Control':
                        flg |= Quartz.kCGEventFlagMaskControl
                    if mkey == 'Alternate':
                        flg |= Quartz.kCGEventFlagMaskAlternate
            if flg:
                Quartz.CGEventSetFlags(event, flg)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)

        except KeyError:
            raise RuntimeError("Key {} not implemented.".format(key))
