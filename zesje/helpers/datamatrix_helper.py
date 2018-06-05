
def decode_raw_datamatrix(data_in):
    """
    Decode a raw datamatrix string returned by pylibdmtx.
    Somehow for non-pure-ascii data (?) it doesn't decode the data on MacOS with
    libdmtx 0.7.5. See https://github.com/NaturalHistoryMuseum/pylibdmtx/issues/24
    Luckily our encoded data isn't too complicated and this function is enough
    Based on https://en.wikipedia.org/wiki/Data_Matrix#Encoding
    """

    debug = ''
    debug_enabled = False
    out = ''
    done = False

    for char in data_in:
        if char == 0:
            debug += 'Not used\n'
        elif char >= 1 and char <= 128:
            debug += 'ascii: ' + chr(char - 1) + ' ' + str(char) + '\n'
            if not done:
                out += chr(char - 1)
        elif char == 129:
            debug += 'End of message\n'
            done = True
        elif char >= 130 and char <= 229:
            debug += 'digit: ' + str(char - 130) + ' ' + str(char) + '\n'
            if not done:
                out += str(int((char - 130) / 10))
                out += str(int((char - 130) % 10))
        elif char == 230:
            debug += 'Begin C40 encoding\n'
        elif char == 231:
            debug += 'Begin Base 256 encoding\n'
        elif char == 232:
            debug += 'FNC1\n'
        elif char == 233:
            debug += 'Structured append. Allows a message to be split across multiple symbols.\n'
        elif char == 234:
            debug += 'Reader programming\n'
        elif char == 235:
            debug += 'Set high bit of the following character\n'
        elif char == 236:
            debug += '05 Macro\n'
        elif char == 237:
            debug += '06 Macro\n'
        elif char == 238:
            debug += 'Begin ANSI X12 encoding\n'
        elif char == 239:
            debug += 'Begin Text encoding\n'
        elif char == 240:
            debug += 'Begin EDIFACT encoding\n'
        elif char == 241:
            debug += 'Extended Channel Interpretation code\n'
        elif char >= 242 and char <= 255:
            debug += 'not used\n'
        else:
            debug += 'dunno: \n' + str(char)

    if debug_enabled:
        print(debug)
    return out
