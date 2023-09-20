import asyncio
from asyncua import Client

async def update_interval_and_led_control():
    # Conectar ao servidor
    url = "opc.tcp://localhost:4840"
    print(f"Conectando ao servidor OPC UA no {url}...")
    async with Client(url=url) as client:
        print("Conectado!")

        # Pegar as variáveis
        uri = 'ArduinoAndTektronix'
        idx = await client.get_namespace_index(uri)
        
        update_interval_var = await client.nodes.root.get_child(["0:Objects", f"{idx}:UpdateInterval"])
        led_status_var = await client.nodes.root.get_child(["0:Objects", f"{idx}:LEDStatus"])
        led_pin_var = await client.nodes.root.get_child(["0:Objects", f"{idx}:LEDPin"])

        # Loop para atualizar o intervalo de atualização e o estado do LED periodicamente
        while True:
            try:
                # Trabalhar com o intervalo de atualização
                current_interval = await update_interval_var.read_value()
                print(f"Intervalo de atualização atual: {current_interval}s")
                new_interval = float(input("Digite o novo intervalo de atualização em segundos: "))
                await update_interval_var.write_value(new_interval)
                print(f"Novo intervalo de atualização definido: {new_interval}s")
                
                # Trabalhar com o estado do LED
                current_led_status = await led_status_var.read_value()
                print(f"Estado atual do LED: {'Ligado' if current_led_status else 'Desligado'}")
                new_led_status = bool(int(input("Digite o novo estado do LED (1 para ligado, 0 para desligado): ")))
                await led_status_var.write_value(new_led_status)
                print(f"Novo estado do LED definido: {'Ligado' if new_led_status else 'Desligado'}")
                
                # Trabalhar com o pino do LED
                current_led_pin = await led_pin_var.read_value()
                print(f"Pino atual do LED: {current_led_pin}")
                new_led_pin = int(input("Digite o novo pino do LED: "))
                await led_pin_var.write_value(new_led_pin)
                print(f"Novo pino do LED definido: {new_led_pin}")
                
                await asyncio.sleep(1)
                
            except KeyboardInterrupt:
                print("Encerrando o cliente.")
                break

if __name__ == "__main__":
    asyncio.run(update_interval_and_led_control())
