import asyncio
import socket
import ssl
import uuid
import struct
from zeroconf.asyncio import AsyncZeroconf, AsyncServiceInfo

# --- CONFIGURATION ---
FRIENDLY_NAME = "Z-DEBUG-BRIDGE"
LOCAL_IP = "192.168.1.31"
PORT = 8009

# Simulation simplifiée d'un message PONG en binaire (CastV2 Protobuf)
# Un vrai message CastV2 est : [Longueur (4 octets)] + [Payload Protobuf]
PONG_MESSAGE = bytes.fromhex("000000410800120873656e6465722d301a0872656365697665722d30222a75726e3a782d636173743a636f6d2e676f6f676c652e636173742e74702e6865617274626561742800320a7b2274797065223a22504f4e47227d")

async def handle_client(reader, writer):
    print(f"[+] Connexion TLS de {writer.get_extra_info('peername')}")
    try:
        while True:
            # Lire la longueur du message (4 octets, Big Endian)
            header = await reader.read(4)
            if not header: break
            
            message_len = struct.unpack(">I", header)[0]
            payload = await reader.read(message_len)
            
            # Debug: voir si on reçoit un PING
            if b"PING" in payload:
                print("[*] PING reçu, envoi du PONG...")
                writer.write(PONG_MESSAGE)
                await writer.drain()
            else:
                print(f"[*] Message reçu ({message_len} octets)")

    except Exception as e:
        print(f"[-] Erreur: {e}")
    finally:
        writer.close()

async def main():
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")

    aiozc = AsyncZeroconf()
    # On force les capacités à "Audio Only" (plus simple pour YT Music au début)
    desc = {
        'id': str(uuid.uuid4()).replace('-', ''),
        'cd': 'DE931514', 
        'fn': FRIENDLY_NAME,
        'md': 'Google Home Mini',
        'st': '0',
        'ca': '199013', 
        've': '05',
    }

    info = AsyncServiceInfo(
        "_googlecast._tcp.local.",
        f"{FRIENDLY_NAME}._googlecast._tcp.local.",
        addresses=[socket.inet_aton(LOCAL_IP)],
        port=PORT,
        properties=desc,
        server="googlecast.local.",
    )

    await aiozc.async_register_service(info)
    
    try:
        server = await asyncio.start_server(handle_client, LOCAL_IP, PORT, ssl=ssl_context)
        print(f"[*] Serveur prêt et réactif aux Pings.")
        async with server:
            await server.serve_forever()
    finally:
        await aiozc.async_unregister_service(info)
        await aiozc.async_close()

if __name__ == "__main__":
    asyncio.run(main())