################################ INITIALIZATION ################################
# Importing required libraries
import asyncio
from asyncua import Server, ua
import pyvisa
import serial_asyncio

# Main asynchronous function
async def main():
    ############################ OPC UA SERVER SETUP ############################
    print("Debug: Iniciando servidor OPC UA...")
    server = Server()
    await server.init()
    server.set_endpoint("opc.tcp://localhost:4840")
    uri = await server.register_namespace("ArduinoAndTektronix")
    print(f"Debug: Namespace registrado: {uri}")

    ############################# ADD VARIABLES #################################

    # Adding variables to OPC UA server
    voltage_var = await server.nodes.objects.add_variable(uri, "AverageVoltage", 0.0)
    print("Debug: Variável de tensão média adicionada.")
    await voltage_var.set_attr_bit(ua.AttributeIds.AccessLevel, ua.AccessLevel.CurrentRead | ua.AccessLevel.HistoryRead)
    await voltage_var.set_attr_bit(ua.AttributeIds.UserAccessLevel, ua.AccessLevel.CurrentRead | ua.AccessLevel.HistoryRead)
    await voltage_var.write_attribute(ua.AttributeIds.Historizing, ua.DataValue(True))

    arduino_var = await server.nodes.objects.add_variable(uri, "ArduinoData", 0.0)
    print("Debug: Variável do Arduino adicionada.")

    update_interval_var = await server.nodes.objects.add_variable(uri, "UpdateInterval", 5.0)
    print("Debug: Variável de intervalo de atualização adicionada.")

    led_status_var = await server.nodes.objects.add_variable(uri, "LEDStatus", False)
    print("Debug: Variável de status do LED adicionada.")

    led_pin_var = await server.nodes.objects.add_variable(uri, "LEDPin", 13)
    print("Debug: Variável de pino do LED adicionada.")

    # Make variables writable
    await update_interval_var.set_writable()
    await led_status_var.set_writable()
    await led_pin_var.set_writable()

    ############################## DEVICE SETUP #################################
    # Connect to Tektronix
    rm = pyvisa.ResourceManager()
    tektronix = rm.open_resource("USB0::0x0699::0x0368::C044865::INSTR")
    tektronix.timeout = 2000  # Setting a timeout can be helpful.
    print("Debug: Conectado ao Tektronix via USB.")
    
    # Connect to Arduino
    reader, writer = await serial_asyncio.open_serial_connection(url='COM6', baudrate=9600)
    print("Debug: Conectado ao Arduino via porta serial.")
    
    await asyncio.sleep(2)
    
    ################################ START SERVER ###############################
    await server.start()
    print("Debug: Servidor OPC UA iniciado.")

    # Enable history for voltage_var with a maximum of 100 values
    await server.historize_node_data_change(voltage_var, period=None, count=100)
    
    ################################ MAIN LOOP ##################################
    try:
        while True:
            # Read and update voltage from Tektronix
            tektronix.write('MEASUrement:IMMed:TYPe MEAN')
            avg_voltage = float(tektronix.query('MEASUrement:IMMed:VALue?'))
            print(f"Debug: Tensão Média lida do Tektronix: {avg_voltage}V")
            await voltage_var.write_value(avg_voltage)
            print(f"Debug: Tensão Média atualizada no servidor OPC UA: {avg_voltage}V")

            # Read and control LED status and pin
            led_status = await led_status_var.read_value()
            await asyncio.sleep(0.1)
            led_pin = await led_pin_var.read_value()
            print(f"Debug: Estado e pino do LED lidos do servidor: {led_status}, {led_pin}")
            
            # Simplified LED command
            cmd = "on" if led_status else "off"
            writer.write(f"{cmd}{led_pin}".encode('utf-8'))
            print(f"Debug: LED no pino {led_pin} {'ligado' if led_status else 'desligado'}.")
            await asyncio.sleep(0.1)

            # Read and update Arduino data
            try:
                writer.write("A0?".encode('utf-8'))
                await asyncio.sleep(0.1)
                line = await reader.readuntil(b'\n')
                arduino_data = float(line.decode().strip())
                await arduino_var.write_value(arduino_data)
                await asyncio.sleep(0.1)
                print(f"Debug: Dado do Arduino atualizado no servidor: {arduino_data}")
            except Exception as e:
                print(f"Debug: Erro ao comunicar com o Arduino: {e}")

            # Read and implement update interval
            update_interval = await update_interval_var.read_value()
            print(f"Debug: Intervalo de atualização lido do servidor: {update_interval}s")
            
            await asyncio.sleep(update_interval)
            print(f"Debug: Esperando {update_interval}s para a próxima atualização.")
            
    except (KeyboardInterrupt, asyncio.CancelledError):
        ########################## SHUTDOWN PROCEDURES ############################
        await server.stop()
        tektronix.close()
        writer.close()
        print("Debug: Servidor OPC UA encerrado.")

################################### MAIN #######################################
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Debug: Programa interrompido pelo usuário.")