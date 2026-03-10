import pyvisa
import numpy as np
import csv
import struct
import time

IP = "192.168.137.220"

rm = pyvisa.ResourceManager()
scope = rm.open_resource(f"TCPIP0::{IP}::inst0::INSTR")

scope.timeout = 5000
scope.chunk_size = 1024000

print(scope.query("*IDN?"))

# ================================
# FUNZIONE ACQUISIZIONE
# ================================

def acquire_waveform(channel=1):

    ch = f"C{channel}"

    print(f"\n--- Acquisisco {ch} ---")

    # Stop acquisizione per stabilità
    scope.write("STOP")
    time.sleep(0.5)

    # Seleziona sorgente
    scope.write(f"WAV:SOUR {ch}")

    # Formato binario
    scope.write("WAV:FORM BYTE")

    # Legge preambolo
    pre = scope.query("WAV:PRE?").strip()
    print("PRE:", pre)

    p = pre.split(',')

    # Parsing tipico SDS
    fmt        = int(p[0])
    typ        = int(p[1])
    points     = int(p[2])
    count      = int(p[3])
    xinc       = float(p[4])
    xorigin    = float(p[5])
    xref       = float(p[6])
    yinc       = float(p[7])
    yorigin    = float(p[8])
    yref       = float(p[9])

    print("Punti:", points)
    print("X increment:", xinc)
    print("Y increment:", yinc)

    # Richiesta dati
    scope.write("WAV:DATA?")
    raw = scope.read_raw()

    # Parsing header binario
    header_len = int(raw[1:2])
    data_len = int(raw[2:2+header_len])

    data = raw[2+header_len : 2+header_len+data_len]

    samples = np.array(struct.unpack(f"{data_len}B", data))

    # Conversione a Volt
    volts = (samples - yref) * yinc + yorigin

    # Conversione a secondi
    times = (np.arange(len(volts)) - xref) * xinc + xorigin

    return times, volts

# ================================
# ACQUISIZIONE
# ================================

t, v = acquire_waveform(1)

scope.write("RUN")

print("\n--- Salvo CSV ---")

with open("waveform_CH1.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["time_s", "voltage_V"])
    for ti, vi in zip(t, v):
        writer.writerow([ti, vi])

print("✔ CSV salvato come waveform_CH1.csv")

scope.close()