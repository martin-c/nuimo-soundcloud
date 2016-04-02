from websocket import create_connection
ws = create_connection('ws://localhost:8080/')
print "Sending data to device"
ws.send('    *    ' +
        '   ***   ' +
        '  *****  ' +
        ' ******* ' +
        '*********' +
        ' ******* ' +
        '  *****  ' +
        '   ***   ' +
        '    *    ')
print "Sent"
print "Receiving..."
result = ws.recv()
print "Received '%s'" % result
ws.close()