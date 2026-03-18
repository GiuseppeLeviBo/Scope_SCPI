import pyvisa
import numpy as np
import struct
import matplotlib
import matplotlib.pyplot as plt
import csv
import time

matplotlib.use("TkAgg")

IP = "192.168.137.220"

# Alcuni firmware Siglent SDS1000 DL/CML restituiscono un vertical_gain
# dimezzato. Lasciamo il workaround esplicito e configurabile, invece di
# rimuoverlo silenziosamente. Imposta a 1.0 per disattivarlo.
SIGLENT_FIRMWARE_GAIN_FIX_FACTOR = 2.0

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

    scope.write("WFSU SP,0")
    scope.write("WFSU NP,0")

    print(f"\nLeggo descriptor {ch}")

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
    print("Vertical gain:", v_gain)
    print("Vertical offset:", v_offset)
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
    # Formula dal descriptor WAVEDESC: tensione = campione * vertical_gain - vertical_offset
    # Non va moltiplicata di nuovo per l'attenuazione della sonda: quel fattore è
    # già incorporato nei parametri verticali restituiti dallo strumento.
    volts = samples.astype(np.float32) * v_gain - v_offset

    # Workaround esplicito per il noto bug firmware Siglent SDS1000 DL/CML.
    # Se il tuo strumento non mostra il problema, imposta
    # SIGLENT_FIRMWARE_GAIN_FIX_FACTOR = 1.0.
    if SIGLENT_FIRMWARE_GAIN_FIX_FACTOR != 1.0:
        print("Applying firmware gain fix factor:", SIGLENT_FIRMWARE_GAIN_FIX_FACTOR)
        volts = volts * SIGLENT_FIRMWARE_GAIN_FIX_FACTOR
    time_axis = np.arange(len(volts)) * h_int + h_off

    return time_axis, volts


print("\nAvvio Auto Setup (ASET)...")
scope.write("ASET")
time.sleep(6)  # Attendiamo il termine dell'autosetup e stabilizzazione del trigger

print("\nSTOP acquisition")
scope.write("STOP")
time.sleep(1)

print("\nAcquisisco CH1...")
t1, v1 = acquire(1)

print("\nAcquisisco CH2...")
t2, v2 = acquire(2)

print("\nRiprendo l'acquisizione (RUN)")
scope.write("RUN")

print("\nCH1 samples:", len(v1), "min:", np.min(v1), "max:", np.max(v1))
print("CH2 samples:", len(v2), "min:", np.min(v2), "max:", np.max(v2))

# Calcolo dello sfasamento / ritardo temporale usando cross-correlazione (ritardo di CH2 rispetto a CH1)
if len(v1) > 0 and len(v2) > 0:
    corr = np.correlate(v1 - np.mean(v1), v2 - np.mean(v2), mode="full")
    delay_idx = np.argmax(corr) - (len(v2) - 1)
    dt = t1[1] - t1[0] if len(t1) > 1 else 1.0
    time_delay = delay_idx * dt
    print(f"\nRitardo temporale stimato CH2 vs CH1: {time_delay:.6e} s")
else:
    time_delay = 0.0

print("\nSalvo CSV")


def format_csv_value(value):
    # Usiamo una stringa in notazione scientifica per evitare che l'apertura del
    # file in Excel/LibreOffice cambi la rappresentazione dei float piccoli.
    return f"{float(value):.9e}"


with open("waveform.csv", "w", newline="", encoding="utf-8") as f:

    # In locale italiano i fogli di calcolo interpretano molto meglio il CSV con
    # separatore ';' rispetto alla virgola quando i numeri usano il punto decimale.
    writer = csv.writer(f, delimiter=";")
    writer.writerow(["time_s", "voltage_CH1_V", "voltage_CH2_V"])

    length = min(len(t1), len(t2))
    for i in range(length):
        writer.writerow([
            format_csv_value(t1[i]),
            format_csv_value(v1[i]),
            format_csv_value(v2[i]),
        ])

print("CSV salvato")

plt.plot(t1, v1, label="CH1")
plt.plot(t2, v2, label="CH2")
plt.xlabel("time (s)")
plt.ylabel("voltage (V)")
plt.title(f"Oscilloscope waveforms\nFase/Ritardo: {time_delay:.2e} s")
plt.legend()
plt.show()

scope.write(":SYSTEM:LOCAL")
scope.close()
