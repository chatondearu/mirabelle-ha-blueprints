{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = [
    pkgs.openssl  # Ajout de l'utilitaire openssl
    (pkgs.python3.withPackages (ps: with ps; [
      zeroconf
      protobuf
      cryptography
    ]))
  ];

  shellHook = ''
    echo "--- Environnement HASS-Cast-Bridge (avec OpenSSL) ---"
    # Génération automatique si les fichiers sont absents
    if [ ! -f cert.pem ]; then
      echo "Génération des certificats TLS temporaires..."
      openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -sha256 -days 365 -nodes -subj "/C=FR/ST=Paris/L=Paris/O=Dev/CN=googlecast.local"
    fi
  '';
}