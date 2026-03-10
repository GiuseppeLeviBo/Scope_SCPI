import pyvisa
import numpy as np
import struct
import matplotlib
import matplotlib.pyplot as plt
import csv
import time

matplotlib.use("TkAgg")

IP = "192.168.137.220"

rm = pyvisa.ResourceManager()
scope = rm.open_resource(f"TCPIP0::{IP}::inst0::INSTR")

scope.timeout = 10000
scope.chunk_size = 2000000

print(scope.query("*IDN?"))

scope.write(":SYSTEM:REMOTE")


def read_scpi_block(raw):

    idx = raw.find(b'#')

    n = int(chr(raw[idx+1]))
    size = int(raw[idx+2:idx+2+n])

    start = idx + 2 + n
    end = start + size

    return raw[start:end]


def acquire(channel=1):

    ch = f"C{channel}"

    print("\nSTOP acquisition")
    scope.write("STOP")
    time.sleep(0.5)
    scope.write("WFSU SP,0")
    scope.write("WFSU NP,0")

    print("Leggo descriptor")

    scope.write(f"{ch}:WF? DESC")
    raw = scope.read_raw()

    desc = read_scpi_block(raw)

    print("Descriptor length:", len(desc))
    print("First 40 bytes:", desc[:40])
    record_len = struct.unpack("<I", desc[116:120])[0]
    print("Record length:", record_len)

    # valori tipici descriptor Lecroy
    v_gain   = struct.unpack("<f", desc[156:160])[0]
    v_offset = struct.unpack("<f", desc[160:164])[0]
    h_int    = struct.unpack("<f", desc[176:180])[0]
    h_off    = struct.unpack("<d", desc[180:188])[0]
    # NOVITA': Leggiamo l'attenuazione della sonda all'offset 328
    probe_att = struct.unpack("<f", desc[328:332])[0]
    print("Vertical gain:", v_gain)
    print("Vertical offset:", v_offset)
    print("Probe attenuation:", probe_att)
    print("Horizontal interval:", h_int)
    sample_rate = 1 / h_int
    print("Sample rate:", sample_rate/1e6, "MS/s")

    duration = record_len * h_int
    print("Time span:", duration, "s")

    print("Scarico waveform")



    scope.write(f"{ch}:WF? DAT2") #  8 bit
#    scope.write(f"{ch}:WF? DAT1")  # 16 bit ?
    raw = scope.read_raw()

    data = read_scpi_block(raw)


    print("Bytes waveform:", len(data))
    comm_type = struct.unpack("<h", desc[32:34])[0]
    if comm_type == 0:
        print("Waveform 8 bit")
        samples = np.frombuffer(data, dtype=np.int8)
    else:
        print("Waveform 16 bit")
        samples = np.frombuffer(data, dtype=np.int16)
    print("raw min:", samples.min())
    print("raw max:", samples.max())
    # Formula corretta: Voltage = Data * v_gain * probe_att - v_offset
    volts = samples.astype(np.float32) * v_gain * probe_att - v_offset
    # Fix per il noto bug firmware Siglent SDS1000 DL/CML
    # Se noti ancora un fattore 2 mancante, l'hardware sta restituendo
    # il guadagno dimezzato nativamente.
    volts = volts * 2.0  # <-- De-commenta questo se probe_att è 1.0 e l'errore persiste
    time_axis = np.arange(len(volts)) * h_int + h_off

    scope.write("RUN")

    return time_axis, volts


t, v = acquire(1)
print("samples:", len(v))
print("min:", np.min(v))
print("max:", np.max(v))
print("Salvo CSV")

with open("waveform.csv","w",newline="") as f:

    writer = csv.writer(f)
    writer.writerow(["time_s","voltage_V"])

    for ti,vi in zip(t,v):
        writer.writerow([ti,vi])

print("CSV salvato")

plt.plot(t,v)
plt.xlabel("time (s)")
plt.ylabel("voltage (V)")
plt.title("Oscilloscope waveform")
plt.show()

scope.write(":SYSTEM:LOCAL")
scope.close()
