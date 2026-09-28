from app.arduino.protocol import parse_weight_message
r=parse_weight_message('{"cells":[{"id":1,"weight":298.5}]}')
assert r[0]["weight"]==298.5
print("Arduino protocol test passed")
