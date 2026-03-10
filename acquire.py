import pyvisa
import time

IP = "192.168.137.220"

rm = pyvisa.ResourceManager()
scope = rm.open_resource(f"TCPIP0::{IP}::inst0::INSTR")

scope.timeout = 5000

print(scope.query("*IDN?"))

# ---- REMOTE CONTROL ----
scope.write(":SYSTEM:REMOTE")

print("\n--- SETUP ---")

scope.write("C1:VDIV 20mV")
scope.write("C2:VDIV 5mV")

scope.write("TDIV 100us")

scope.write("TRMD AUTO")
scope.write("TRSE EDGE")
scope.write("TRSL POS")
scope.write("TRSR C1")

time.sleep(1)

print("C1:", scope.query("C1:VDIV?"))
print("C2:", scope.query("C2:VDIV?"))
print("Timebase:", scope.query("TDIV?"))

print("\n--- ACQUISIZIONE ---")

scope.write("STOP")
time.sleep(0.5)

def get_waveform(channel):

    scope.write(f"WFSU SP,0,NP,0,FP,0")   # setup transfer
    scope.write(f"C{channel}:WF? DAT2")

    raw = scope.read_raw()

    return raw


wf1 = get_waveform(1)
wf2 = get_waveform(2)

print("CH1 bytes:", len(wf1))
print("CH2 bytes:", len(wf2))