import pyvisa
import sys

SCOPE_IP = "192.168.137.220"   # <-- cambia se necessario

try:
    print("Creo Resource Manager...")
    rm = pyvisa.ResourceManager('@py')

    print("Risorse VISA visibili:")
    print(rm.list_resources())

    resource_string = f"TCPIP::{SCOPE_IP}::inst0::INSTR"

    print(f"\nProvo a connettermi a: {resource_string}")
    scope = rm.open_resource(resource_string)

    scope.timeout = 5000
    scope.read_termination = '\n'
    scope.write_termination = '\n'

    print("\nConnessione OK ✅")

    print("\nInvio *IDN?")
    idn = scope.query("*IDN?")
    print("Risposta strumento:")
    print(idn)

except Exception as e:
    print("\n❌ ERRORE:")
    print(e)
    sys.exit(1)