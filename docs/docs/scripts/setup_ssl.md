# SSL Certificate Management Script

The SSL certificate management script (`ggnet2-cert-mgr`) generates self-signed SSL certificates for ggnet2 Nginx configuration.

## Overview

The SSL certificate management script:

- Generates self-signed SSL certificates
- Supports custom DNS and IP addresses
- Automatically adds hostname and IP addresses
- Creates certificates with 10-year validity
- Configures SSL directory structure
- Integrates with Nginx configuration

## Usage

```bash
# Generate self-signed certificate with default settings
sudo ggnet2-cert-mgr generate

# Generate with custom DNS names
sudo ggnet2-cert-mgr generate "ggnet2 ggnet2.local" ""

# Generate with custom IP addresses
sudo ggnet2-cert-mgr generate "" "192.168.1.10 192.168.1.20"

# Generate with both DNS and IP addresses
sudo ggnet2-cert-mgr generate "ggnet2 ggnet2.local" "192.168.1.10 192.168.1.20"
```

## Script Structure

**ggnet2-cert-mgr:**
```bash
#!/bin/bash

function join_by { 
    local d=$1
    shift
    local f=$1
    shift
    printf %s "$f" "${@/#/$d}"
}

generate_self_signed_cert() {
    CUSTOM_DNS=$1
    CUSTOM_IP=$2

    mkdir -p /etc/nginx/ssl/certs
    mkdir -p -m 710 /etc/nginx/ssl/private

    HOSTNAME=$(hostname -f)
    HOSTNAMES=$(hostname -I)

    IP_ALTNAMES=""
    DNS_ALTNAMES=""

    if ! [ -z "$CUSTOM_IP" ]; then
        IP_ALTNAMES=$(join_by ', ' $(printf "IP:%s\n" $CUSTOM_IP))
    fi

    if ! [ -z "$CUSTOM_DNS" ]; then
        DNS_ALTNAMES=$(join_by ', ' $(printf "DNS:%s\n" $CUSTOM_DNS))
    fi

    if [ -z "$IP_ALTNAMES" ] && [ -z "$DNS_ALTNAMES" ]; then
        DNS_ALTNAMES="DNS:localhost"

        if ! [ -z $HOSTNAMES ]; then
            IP_ALTNAMES=$(join_by ', ' $(printf "IP:%s\n" $HOSTNAMES))  
        fi
    fi
    
    ALTNAMES="$DNS_ALTNAMES"

    if ! [ -z "$IP_ALTNAMES" ]; then
        if ! [ -z "$ALTNAMES" ]; then
            ALTNAMES="$ALTNAMES, $IP_ALTNAMES"
        else
            ALTNAMES="$IP_ALTNAMES"
        fi
    fi

    echo "Generating certificate with Subject Alternative Names: $ALTNAMES"

    openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
        -keyout /etc/nginx/ssl/private/ggnet2-self-signed.key \
        -out /etc/nginx/ssl/certs/ggnet2-self-signed.crt \
        -subj "/C=US/O=ggCircuit LLC/OU=ggnet2 Server Default Certificate/CN=$HOSTNAME/emailAddress=info@ggcircuit.com" \
        -addext "subjectAltName = $ALTNAMES"
    
    # Set proper permissions
    chmod 644 /etc/nginx/ssl/certs/ggnet2-self-signed.crt
    chmod 600 /etc/nginx/ssl/private/ggnet2-self-signed.key
    
    echo "Certificate generated successfully"
    echo "Certificate: /etc/nginx/ssl/certs/ggnet2-self-signed.crt"
    echo "Private Key: /etc/nginx/ssl/private/ggnet2-self-signed.key"
}

if [[ $EUID -ne 0 ]]; then
   echo "This tool must be run as root."
   exit 1
fi

case $1 in

generate)
    generate_self_signed_cert "$2" "$3"
    ;;

*)
    cat << EOF
usage: ggnet2-cert-mgr <command>

Commands:
    generate <dns addresses> <ip addresses>   Generate new self-signed certificate. DNS and IP addresses are optional to specify. Example: 'generate "ggnet2 ggnet2.local" "192.168.1.71 192.168.1.77"'
EOF
    exit 1
    ;;

esac
```

## Configuration

### Certificate Details

**Certificate Subject:**
- **Country (C)**: US
- **Organization (O)**: ggCircuit LLC
- **Organizational Unit (OU)**: ggnet2 Server Default Certificate
- **Common Name (CN)**: Hostname (FQDN)
- **Email**: info@ggcircuit.com

**Certificate Validity:**
- **Duration**: 3650 days (10 years)
- **Key Size**: 2048 bits (RSA)
- **Algorithm**: RSA with X.509

**Subject Alternative Names (SAN):**
- Automatically adds `DNS:localhost` if no custom names provided
- Automatically adds all IP addresses from `hostname -I` if no custom IPs provided
- Supports custom DNS names (e.g., `ggnet2`, `ggnet2.local`)
- Supports custom IP addresses (e.g., `192.168.1.10`, `192.168.1.20`)

### Directory Structure

**SSL Directories:**
```
/etc/nginx/ssl/
├── certs/
│   └── ggnet2-self-signed.crt  # Certificate (644)
└── private/
    └── ggnet2-self-signed.key   # Private key (600)
```

**Permissions:**
- Certificate: `644` (readable by all, writable by owner)
- Private Key: `600` (readable/writable by owner only)
- Private Directory: `710` (executable by all, readable/writable by owner)

### Nginx Integration

**SSL Snippet:**
```nginx
include snippets/ggnet2-cert.conf;
```

**SSL Snippet File:**
```
/etc/nginx/snippets/ggnet2-cert.conf

ssl_certificate /etc/nginx/ssl/certs/ggnet2-self-signed.crt;
ssl_certificate_key /etc/nginx/ssl/private/ggnet2-self-signed.key;
```

## Verification

### Check Certificate

```bash
# View certificate details
openssl x509 -in /etc/nginx/ssl/certs/ggnet2-self-signed.crt -text -noout

# View certificate subject
openssl x509 -in /etc/nginx/ssl/certs/ggnet2-self-signed.crt -noout -subject

# View certificate issuer
openssl x509 -in /etc/nginx/ssl/certs/ggnet2-self-signed.crt -noout -issuer

# View certificate validity
openssl x509 -in /etc/nginx/ssl/certs/ggnet2-self-signed.crt -noout -dates

# View Subject Alternative Names
openssl x509 -in /etc/nginx/ssl/certs/ggnet2-self-signed.crt -noout -text | grep -A 2 "Subject Alternative Name"
```

### Check Private Key

```bash
# Check private key
openssl rsa -in /etc/nginx/ssl/private/ggnet2-self-signed.key -check

# View private key details
openssl rsa -in /etc/nginx/ssl/private/ggnet2-self-signed.key -text -noout
```

### Verify Certificate and Key Match

```bash
# Get certificate modulus
openssl x509 -noout -modulus -in /etc/nginx/ssl/certs/ggnet2-self-signed.crt | openssl md5

# Get private key modulus
openssl rsa -noout -modulus -in /etc/nginx/ssl/private/ggnet2-self-signed.key | openssl md5

# Compare (should match)
```

### Test Certificate with Nginx

```bash
# Test Nginx configuration
nginx -t

# Check SSL configuration
nginx -T | grep -A 10 "ssl_certificate"

# Test HTTPS connection
openssl s_client -connect localhost:443 -servername localhost
```

## Troubleshooting

### Certificate Generation Fails

**Check OpenSSL:**
```bash
# Check if OpenSSL is installed
which openssl

# Check OpenSSL version
openssl version

# Test OpenSSL
openssl req -x509 -nodes -days 3650 -newkey rsa:2048 -keyout /tmp/test.key -out /tmp/test.crt -subj "/CN=test"
```

**Check Permissions:**
```bash
# Check directory permissions
ls -la /etc/nginx/ssl/
ls -la /etc/nginx/ssl/certs/
ls -la /etc/nginx/ssl/private/

# Fix permissions if needed
chmod 755 /etc/nginx/ssl
chmod 755 /etc/nginx/ssl/certs
chmod 710 /etc/nginx/ssl/private
```

### Certificate Not Working with Nginx

**Check Nginx Configuration:**
```bash
# Check SSL snippet exists
cat /etc/nginx/snippets/ggnet2-cert.conf

# Check Nginx configuration includes snippet
grep -r "ggnet2-cert.conf" /etc/nginx/

# Check certificate paths in Nginx config
nginx -T | grep "ssl_certificate"

# Test Nginx configuration
nginx -t
```

**Check Certificate Validity:**
```bash
# Check certificate expiration
openssl x509 -in /etc/nginx/ssl/certs/ggnet2-self-signed.crt -noout -enddate

# Check certificate matches hostname
openssl x509 -in /etc/nginx/ssl/certs/ggnet2-self-signed.crt -noout -text | grep -A 2 "Subject Alternative Name"
```

### Certificate and Key Mismatch

**Check Modulus Match:**
```bash
# Compare certificate and key modulus
CERT_MOD=$(openssl x509 -noout -modulus -in /etc/nginx/ssl/certs/ggnet2-self-signed.crt | openssl md5)
KEY_MOD=$(openssl rsa -noout -modulus -in /etc/nginx/ssl/private/ggnet2-self-signed.key | openssl md5)

if [ "$CERT_MOD" = "$KEY_MOD" ]; then
    echo "Certificate and key match"
else
    echo "Certificate and key do NOT match"
    echo "Regenerating certificate..."
    ggnet2-cert-mgr generate
fi
```

## Development Notes

- Certificate generation uses OpenSSL
- Certificates are valid for 10 years (3650 days)
- RSA key size is 2048 bits
- Subject Alternative Names are automatically added
- Certificate and key are stored in separate directories
- Permissions are set for security (600 for private key)
- SSL snippet is created automatically by Nginx setup script

## Security Considerations

- **Self-Signed Certificates**: Suitable for development and internal use
- **Production Use**: Consider using Let's Encrypt or commercial certificates
- **Private Key Security**: Private key is stored with 600 permissions (owner-only access)
- **Certificate Validity**: 10-year validity reduces maintenance but increases security risk
- **Key Size**: 2048-bit RSA is considered secure but consider 4096-bit for production

## To-Do

- [ ] Implement Let's Encrypt integration
- [ ] Add certificate renewal automation
- [ ] Add certificate revocation support
- [ ] Implement certificate chain support
- [ ] Add wildcard certificate support
- [ ] Implement certificate backup/restore

