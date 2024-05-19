import MultiPyVu as mpv

server = mpv.Server().open()
client = mpv.Client(host='127.0.0.1', port=5000)
client.open()
running = True

while running:
    T, sT = client.get_temperature()
    print(T, sT)