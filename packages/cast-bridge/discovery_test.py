import asyncio
import socket
import ssl
import uuid
from zeroconf.asyncio import AsyncZeroconf, AsyncServiceInfo

# --- CONFIGURATION ---
FRIENDLY_NAME = "MA Bridge"
LOCAL_IP = "192.168.1.31" # <--- VÉRIFIEZ BIEN
PORT = 8009

async def handle_client(reader, writer):
    print(f"[+] Connexion TLS établie avec succès !")
    try:
        while True:
            data = await reader.read(1024)
            if not data: break
            # Ici on recevra les PING de YouTube Music
            print(f"[*] Reçu (chiffré): {data.hex()[:20]}...")
    except Exception as e:
        print(f"[-] Erreur client: {e}")
    finally:
        writer.close()

async def main():
    # Configuration SSL pour satisfaire YouTube Music
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")

    aiozc = AsyncZeroconf()
    # Default desc with video and audio capabilities
    # desc = {
    #     'id': str(uuid.uuid4()).replace('-', ''),
    #     'cd': 'DE931514', # Application YouTube Music
    #     'fn': FRIENDLY_NAME,
    #     'md': 'Chromecast Ultra',
    #     'st': '0',
    #     'ca': '199013', # Capacités étendues (Audio/Video/Large)
    #     've': '05',
    # }

    # Desc with only audio capabilities
    desc = {
        'id': str(uuid.uuid4()).replace('-', ''),
        'cd': 'DE931514', 
        'fn': FRIENDLY_NAME,
        'md': 'Google Home Mini', # Changement de modèle
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
        # On lance le serveur AVEC le contexte SSL
        server = await asyncio.start_server(
            handle_client, LOCAL_IP, PORT, ssl=ssl_context
        )
        print(f"[*] Serveur TLS prêt sur {LOCAL_IP}:{PORT}")
        async with server:
            await server.serve_forever()
    finally:
        await aiozc.async_unregister_service(info)
        await aiozc.async_close()

if __name__ == "__main__":
    asyncio.run(main())