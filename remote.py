import pyvisa

rm = pyvisa.ResourceManager()

scope = rm.open_resource("TCPIP::192.168.137.220::inst0::INSTR")

scope.timeout = 5000
scope.write_termination = '\n'
scope.read_termination = '\n'

print("Connessione vera:", scope.resource_name)
print("Scope trovato:", scope.query("*IDN?"))

print("\n--- Prendo controllo remoto ---")
scope.write(":SYSTEM:REMOTE")
scope.write(":LOCK ON")

print("\n--- Leggo scala CH1 attuale ---")
print("CH1 scale:", scope.query(":CHAN1:SCAL?"))

print("\n--- Imposto CH1 = 20mV/div ---")
scope.write(":CHAN1:SCAL 0.02")

print("\n--- Rileggo CH1 ---")
print("CH1 scale:", scope.query(":CHAN1:SCAL?"))
scope.write(":CHANnel1:SCALe 0.02")
print(scope.query(":CHANnel1:SCALe?"))
scope.write(":TRIG:MODE AUTO")