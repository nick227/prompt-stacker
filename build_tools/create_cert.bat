@echo off
echo.
echo ========================================
echo    CREATING FREE SELF-SIGNED CERTIFICATE
echo ========================================
echo.

echo [1/3] Creating private key...
openssl genrsa -out promptstacker.key 2048
if errorlevel 1 (
    echo   ❌ Failed to create private key
    pause
    exit /b 1
)
echo   ✓ Private key created: promptstacker.key

echo.
echo [2/3] Creating certificate signing request...
openssl req -new -key promptstacker.key -out promptstacker.csr -subj "/CN=Prompt Stacker Developer/OU=Development/O=Prompt Stacker Project/C=US"
if errorlevel 1 (
    echo   ❌ Failed to create CSR
    pause
    exit /b 1
)
echo   ✓ CSR created: promptstacker.csr

echo.
echo [3/3] Creating self-signed certificate...
openssl x509 -req -days 365 -in promptstacker.csr -signkey promptstacker.key -out promptstacker.crt
if errorlevel 1 (
    echo   ❌ Failed to create certificate
    pause
    exit /b 1
)
echo   ✓ Certificate created: promptstacker.crt

echo.
echo [4/4] Converting to PFX format for Windows...
openssl pkcs12 -export -out promptstacker.pfx -inkey promptstacker.key -in promptstacker.crt -passout pass:promptstacker
if errorlevel 1 (
    echo   ❌ Failed to create PFX
    pause
    exit /b 1
)
echo   ✓ PFX certificate created: promptstacker.pfx

echo.
echo ========================================
echo           CERTIFICATE READY!
echo ========================================
echo.
echo 🎉 Your free self-signed certificate is ready!
echo 📁 Files created:
echo   - promptstacker.key (private key)
echo   - promptstacker.csr (certificate request)
echo   - promptstacker.crt (certificate)
echo   - promptstacker.pfx (Windows format)
echo.
echo 🔐 Password: promptstacker
echo.
echo ⚠️  Note: This is a self-signed certificate.
echo    Windows will still show warnings, but it's better than unsigned!
echo.
pause
