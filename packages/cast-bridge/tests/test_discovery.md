# Setup

run `nix-shell`

create a temp certificat

```bash
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -sha256 -days 365 -nodes -subj "/C=FR/ST=Paris/L=Paris/O=Dev/CN=googlecast.local" && echo "Certificats créés avec succès !"
```

