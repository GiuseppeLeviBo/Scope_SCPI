import pyvisa

rm = pyvisa.ResourceManager()
scope = rm.open_resource("TCPIP0::192.168.137.220::inst0::INSTR")

scope.timeout = 5000

print(scope.query("*IDN?"))

scope.write(":SYSTEM:REMOTE")

print("VDIV attuale:", scope.query("C1:VDIV?"))

scope.write("C1:VDIV 20mV")

print("VDIV nuovo:", scope.query("C1:VDIV?"))

scope.write(":SYSTEM:LOCAL")
