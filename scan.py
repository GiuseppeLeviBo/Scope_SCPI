import pyvisa

def find_scopes():
    rm = pyvisa.ResourceManager('@py')
    resources = rm.list_resources()

    scopes = []

    for res in resources:
        if "TCPIP" in res:
            try:
                inst = rm.open_resource(res)
                idn = inst.query("*IDN?")
                if "RSDS" in idn:
                    scopes.append((res, idn.strip()))
            except:
                pass

    return scopes


scopes = find_scopes()

if not scopes:
    print("Nessuno scope trovato")
else:
    print("Scope trovati:")
    for r, idn in scopes:
        print(r, "->", idn)