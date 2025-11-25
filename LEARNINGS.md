# Code Signing Learnings for EasyOTP

This document captures the lessons learned while setting up automated code signing for Windows executables using GitHub Actions. This was a painful process with many gotchas - documenting everything here to avoid repeating mistakes.

## Overview

The goal was to:
1. Build a Windows executable using PyInstaller in GitHub Actions
2. Sign the executable with a self-signed certificate
3. Provide users with options to trust the certificate or run unsigned

## Key Learnings

### 1. Self-Signed Certificate Must Have Code Signing EKU

**Problem**: A generic self-signed certificate won't work for code signing.

**Solution**: When creating the certificate, you MUST use `-Type CodeSigningCert`:

```powershell
# WRONG - creates a generic certificate that signtool won't recognize
New-SelfSignedCertificate -Subject "CN=MyApp" -CertStoreLocation "Cert:\CurrentUser\My"

# CORRECT - creates a code signing certificate with proper EKU
New-SelfSignedCertificate -Subject "CN=MyApp" -Type CodeSigningCert -CertStoreLocation "Cert:\CurrentUser\My"
```

The certificate must have the Enhanced Key Usage (EKU) of "Code Signing (1.3.6.1.5.5.7.3.3)".

### 2. Certificate Subject Fields (X.500 DN)

You can include multiple fields in the certificate subject to provide identity information:

```powershell
New-SelfSignedCertificate `
    -Subject "CN=EasyOTP, O=Raymond Clowe, OU=Github: raymondclowe, C=CN, S=Hong Kong, L=Hong Kong" `
    -Type CodeSigningCert `
    -CertStoreLocation "Cert:\CurrentUser\My" `
    -KeyExportPolicy Exportable `
    -KeyLength 2048 `
    -KeyAlgorithm RSA `
    -HashAlgorithm SHA256 `
    -NotAfter (Get-Date).AddYears(3)
```

Common fields:
- **CN** (Common Name): App or developer name
- **O** (Organization): Your name or company
- **OU** (Organizational Unit): Can include GitHub username for OSS credibility
- **C** (Country): Two-letter country code
- **S** or **ST** (State/Province)
- **L** (Locality/City)

### 3. Exporting the Certificate

Export the PFX (private key + certificate) for signing:

```powershell
$password = ConvertTo-SecureString -String "YourSecurePassword!" -Force -AsPlainText
Export-PfxCertificate -Cert "Cert:\CurrentUser\My\<THUMBPRINT>" -FilePath MyApp.pfx -Password $password
```

Export the CER (public certificate only) for users to import:

```powershell
Export-Certificate -Cert "Cert:\CurrentUser\My\<THUMBPRINT>" -FilePath MyApp.cer
```

**IMPORTANT**: 
- The `.pfx` file is SECRET - never commit it to the repo
- The `.cer` file is PUBLIC - safe to commit and share
- Add `*.pfx` to `.gitignore`

### 4. Storing the Certificate in GitHub Secrets

The PFX must be base64-encoded to store as a GitHub secret:

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("MyApp.pfx")) | Set-Clipboard
```

Then create two GitHub secrets:
- `CERT_PFX`: The base64-encoded PFX content
- `CERT_PASSWORD`: The password used when exporting the PFX

**Gotcha**: Watch out for trailing spaces when pasting! This caused "invalid password" errors.

### 5. Decoding the Certificate in GitHub Actions

Use `certutil` to decode, not PowerShell's `[Convert]::FromBase64String()`:

```yaml
- name: Decode certificate
  run: |
    New-Item -ItemType directory -Path certificate
    Set-Content -Path certificate\certificate.txt -Value "${{ secrets.CERT_PFX }}"
    certutil -decode certificate\certificate.txt certificate\certificate.pfx
```

**Why**: PowerShell's base64 decoding had issues with certain content; `certutil` is more reliable.

### 6. Import Certificate to Store Before Signing

signtool works better when the certificate is in the Windows certificate store:

```yaml
- name: Decode and import certificate
  env:
    CERT_PASSWORD: ${{ secrets.CERT_PASSWORD }}
  run: |
    New-Item -ItemType directory -Path certificate
    Set-Content -Path certificate\certificate.txt -Value "${{ secrets.CERT_PFX }}"
    certutil -decode certificate\certificate.txt certificate\certificate.pfx
    
    $securePassword = ConvertTo-SecureString -String $env:CERT_PASSWORD -Force -AsPlainText
    $cert = Import-PfxCertificate -FilePath certificate\certificate.pfx -CertStoreLocation Cert:\CurrentUser\My -Password $securePassword
    Write-Host "Imported certificate thumbprint: $($cert.Thumbprint)"
```

### 7. Finding signtool on GitHub Runners

signtool is NOT in the PATH on GitHub Windows runners. You must find it:

```yaml
- name: Sign executable
  run: |
    $signtool = Get-ChildItem -Path "C:\Program Files (x86)\Windows Kits\10\bin\*\x64\signtool.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    $cert = Get-ChildItem -Path Cert:\CurrentUser\My -CodeSigningCert | Select-Object -First 1
    & $signtool.FullName sign /sha1 $cert.Thumbprint /fd SHA256 /tr http://timestamp.digicert.com /td sha256 dist\MyApp.exe
```

### 8. signtool Requires SHA256 Flag

Modern signtool requires explicit digest algorithm:

```
SignTool Error: No file digest algorithm specified.
```

**Solution**: Always include `/fd SHA256`:

```powershell
signtool sign /sha1 <thumbprint> /fd SHA256 /tr http://timestamp.digicert.com /td sha256 MyApp.exe
```

### 9. Use Thumbprint Instead of PFX File

Using the certificate thumbprint (`/sha1`) after importing to the store is more reliable than using the PFX file directly (`/f`):

```powershell
# Less reliable
signtool sign /f cert.pfx /p password /fd SHA256 ...

# More reliable
signtool sign /sha1 <thumbprint> /fd SHA256 ...
```

### 10. Timestamp the Signature

Always timestamp your signatures so they remain valid after the certificate expires:

```powershell
signtool sign /sha1 <thumbprint> /fd SHA256 /tr http://timestamp.digicert.com /td sha256 MyApp.exe
```

Use `/tr` (RFC 3161 timestamp) with `/td sha256` for modern timestamping.

### 11. Cleanup Sensitive Files

Always clean up certificate files after signing:

```yaml
- name: Cleanup certificate files
  if: always()
  run: |
    Remove-Item -Recurse -Force certificate -ErrorAction SilentlyContinue
    Get-ChildItem -Path Cert:\CurrentUser\My | Where-Object { $_.Subject -like "*EasyOTP*" } | Remove-Item -ErrorAction SilentlyContinue
```

## Complete Working Workflow

See `.github/workflows/build-windows.yml` for the complete working implementation.

## Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `signtool: The term 'signtool' is not recognized` | signtool not in PATH | Use full path from Windows Kits |
| `No certificates were found that met all the given criteria` | Wrong password, corrupted PFX, or missing Code Signing EKU | Verify password, re-export PFX, ensure `-Type CodeSigningCert` |
| `No file digest algorithm specified` | Missing /fd flag | Add `/fd SHA256` |
| `No code signing certificate found in store` | Certificate missing Code Signing EKU | Recreate with `-Type CodeSigningCert` |
| `The specified network password is not correct` | Wrong password in secret | Check for trailing spaces, verify password matches |

## Files

- `EasyOTP.cer` - Public certificate (safe to share, users import this to trust)
- `EasyOTP.pfx` / `EasyOTP_CodeSign.pfx` - Private key + certificate (SECRET, never commit)
- `.github/workflows/build-windows.yml` - GitHub Actions workflow

## Self-Signed vs Commercial Certificates

Self-signed certificates:
- ✅ Free
- ✅ You control it
- ❌ Windows SmartScreen will still warn users
- ❌ Users must manually trust or click "Run anyway"

Commercial code signing certificates:
- ❌ Cost money (~$200-500/year)
- ✅ Recognized by Windows immediately
- ✅ No SmartScreen warnings after reputation builds
- ✅ Extended Validation (EV) certs never show warnings

For open source projects, self-signed with good documentation is acceptable.

## References

- [Federico Terzi's Guide to Code Signing on GitHub Actions](https://federicoterzi.com/blog/automatic-codesigning-on-windows-using-github-actions/)
- [Microsoft SignTool Documentation](https://docs.microsoft.com/en-us/windows/win32/seccrypto/signtool)
- [New-SelfSignedCertificate Documentation](https://docs.microsoft.com/en-us/powershell/module/pki/new-selfsignedcertificate)
