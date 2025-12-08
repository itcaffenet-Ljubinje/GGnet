# ggnet2-cert-mgr Script

**Datum kreiranja:** 2025-01-26  
**Status:** 📋 SSL Certificate Management Script Documentation

---

## 📊 Pregled

`ggnet2-cert-mgr` je bash skripta za upravljanje SSL sertifikatima. Generiše self-signed SSL sertifikate za Nginx sa custom DNS i IP adresama.

---

## 🚀 Usage

### Basic Usage

```bash
sudo ggnet2-cert-mgr generate
```

### With Custom DNS Addresses

```bash
sudo ggnet2-cert-mgr generate "ggnet2 ggnet2.local"
```

### With Custom IP Addresses

```bash
sudo ggnet2-cert-mgr generate "" "192.168.1.100 192.168.1.101"
```

### With Both DNS and IP Addresses

```bash
sudo ggnet2-cert-mgr generate "ggnet2 ggnet2.local" "192.168.1.100 192.168.1.101"
```

---

## 🔧 Kako Radi

### 1. Auto-Detection

Ako ne specificirate DNS ili IP adrese, skripta automatski:
- Koristi `hostname -f` za hostname
- Koristi `hostname -I` za sve IP adrese servera
- Dodaje `localhost` kao DNS alternativu

### 2. Certificate Generation

Skripta generiše:
- **Private Key:** `/etc/nginx/ssl/private/ggnet2-self-signed.key`
- **Certificate:** `/etc/nginx/ssl/certs/ggnet2-self-signed.crt`

**Certificate Details:**
- **Validity:** 10 years (3650 days)
- **Key Size:** RSA 2048 bits
- **Subject:** `/C=US/O=ggNET2/OU=ggNET2 Server Default Certificate/CN=<hostname>/emailAddress=admin@ggnet2.local`
- **Subject Alternative Names:** Automatski dodaje DNS i IP adrese

### 3. Permissions

- **Private Key:** `600` (read/write owner only)
- **Certificate:** `644` (read owner/group, read others)

---

## 📋 Requirements

### System Requirements

- **Debian/Ubuntu** Linux
- **Root privileges** (sudo)
- **OpenSSL** installed

### OpenSSL Installation

```bash
sudo apt-get install -y openssl
```

---

## 🔒 Security

### Self-Signed Certificates

**Napomena:** Self-signed sertifikati nisu verifikovani od strane Certificate Authority (CA). Browser-i će prikazati upozorenje o sigurnosti.

**Za Production:**
- Koristite Let's Encrypt ili drugi CA
- Ili koristite enterprise CA sertifikat

### Certificate Validity

- **Duration:** 10 years (3650 days)
- **Key Size:** RSA 2048 bits (sigurno za većinu slučajeva)

---

## 📝 Example Output

```bash
$ sudo ggnet2-cert-mgr generate "ggnet2.local" "192.168.1.100"

Generating self-signed certificate with subjectAltName: DNS:ggnet2.local, IP:192.168.1.100
Certificate generated successfully:
  Key: /etc/nginx/ssl/private/ggnet2-self-signed.key
  Cert: /etc/nginx/ssl/certs/ggnet2-self-signed.crt
```

---

## 🔄 Nginx Configuration

Nakon generisanja sertifikata, ažurirajte Nginx konfiguraciju:

```nginx
server {
    listen 443 ssl;
    server_name ggnet2.local;

    ssl_certificate /etc/nginx/ssl/certs/ggnet2-self-signed.crt;
    ssl_certificate_key /etc/nginx/ssl/private/ggnet2-self-signed.key;

    # ... rest of configuration
}
```

---

## 🐛 Troubleshooting

### Error: This tool must be run as root

**Problem:**
```
Error: This tool must be run as root (use sudo)
```

**Rešenje:**
```bash
sudo ggnet2-cert-mgr generate
```

### Error: openssl command not found

**Problem:**
```
openssl: command not found
```

**Rešenje:**
```bash
sudo apt-get install -y openssl
```

### Certificate Not Working in Browser

**Problem:** Browser prikazuje upozorenje o sigurnosti

**Rešenje:**
- Ovo je normalno za self-signed sertifikate
- Kliknite "Advanced" → "Proceed to site" (ili slično)
- Za production, koristite Let's Encrypt ili CA sertifikat

---

## 📚 Reference

- **Script Location:** `scripts/ggnet2-cert-mgr`
- **Nginx SSL Configuration:** `docs/scripts/setup_nginx.md`
- **OpenSSL Documentation:** https://www.openssl.org/docs/

---

## ✅ Checklist

- [ ] OpenSSL instaliran
- [ ] Skripta ima execute permissions (`chmod +x scripts/ggnet2-cert-mgr`)
- [ ] Pokrenuta sa `sudo`
- [ ] Certificate generisan (`/etc/nginx/ssl/certs/ggnet2-self-signed.crt`)
- [ ] Private key generisan (`/etc/nginx/ssl/private/ggnet2-self-signed.key`)
- [ ] Permissions postavljeni (key: 600, cert: 644)
- [ ] Nginx konfiguracija ažurirana

---

**ggnet2-cert-mgr Script Complete!** ✅

