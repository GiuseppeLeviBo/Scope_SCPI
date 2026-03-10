import pyvisa
import time

def find_scope():
    rm = pyvisa.ResourceManager('@py')
    for res in rm.list_resources():
        if "TCPIP" in res:
            ip = res.split("::")[1]

            for variant in [
                f"TCPIP::{ip}::inst0::INSTR",
                f"TCPIP0::{ip}::inst0::INSTR"
            ]:
                try:
                    inst = rm.open_resource(variant)
                    idn = inst.query("*IDN?")
                    if "RSDS" in idn:
                        print("Connessione vera:", variant)
                        return inst
                except:
                    pass
    return None


scope = find_scope()

if scope is None:
    print("Scope non trovato")
    exit()

scope.timeout = 5000

print("Scope trovato:", scope.query("*IDN?"))

print("\n--- Leggo scala CH1 attuale ---")
print("CH1 scale:", scope.query(":CHAN1:SCAL?"))

print("\n--- Imposto CH1 = 20mV/div ---")
scope.write(":CHAN1:SCAL 0.02")

time.sleep(1)

print("\n--- Rileggo CH1 ---")
print("CH1 scale:", scope.query(":CHAN1:SCAL?"))