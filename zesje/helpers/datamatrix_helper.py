
def decode_raw_datamatrix(data_in):
    """
    Decode a raw datamatrix string returned by pylibdmtx.
    Somehow for non-pure-ascii data (?) it doesn't decode the data on MacOS with
    libdmtx 0.7.5. See https://github.com/NaturalHistoryMuseum/pylibdmtx/issues/24
    Luckily our encoded data isn't too complicated and this function is enough
    Based on https://en.wikipedia.org/wiki/Data_Matrix#Encoding
    """

    out = ''
    done = False

    for char in data_in:
        if char >= 1 and char <= 128:
            #  ascii, but shifted
            if not done:
                out += chr(char - 1)
        elif char == 129:
            #  End of message
            done = True
        elif char >= 130 and char <= 229:
            #  digits, two per character
            if not done:
                out += str(int((char - 130) / 10))
                out += str(int((char - 130) % 10))

        #  Anything else is not understood or after 'End of Message'
        #  which is not supported now as its not
        #  needed for used format.
    return out
