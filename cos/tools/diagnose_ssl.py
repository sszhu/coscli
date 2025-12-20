#!/usr/bin/env python3
"""
SSL Diagnostic Tool for COS CLI
This script helps diagnose SSL certificate issues in corporate environments.
"""

import os
import sys
import ssl
import certifi
from pathlib import Path


def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print('='*60)


def print_section(text):
    print(f"\n{text}")
    print('-' * len(text))


def check_environment_variables():
    """Check SSL-related environment variables"""
    print_section("Environment Variables")
    
    vars_to_check = [
        'REQUESTS_CA_BUNDLE',
        'SSL_CERT_FILE', 
        'CURL_CA_BUNDLE',
        'PYTHONHTTPSVERIFY',
        'HTTP_PROXY',
        'HTTPS_PROXY',
        'NO_PROXY'
    ]
    
    found_any = False
    for var in vars_to_check:
        value = os.environ.get(var)
        if value:
            print(f"✓ {var} = {value}")
            found_any = True
    
    if not found_any:
        print("ℹ No SSL environment variables set")


def check_certifi():
    """Check certifi certificate bundle"""
    print_section("Certifi Certificate Bundle")
    
    try:
        cert_path = certifi.where()
        print(f"✓ Location: {cert_path}")
        
        if Path(cert_path).exists():
            size = Path(cert_path).stat().st_size
            print(f"✓ Size: {size:,} bytes")
            print(f"✓ Bundle exists and is accessible")
        else:
            print(f"❌ Bundle not found at {cert_path}")
    except Exception as e:
        print(f"❌ Error checking certifi: {e}")


def check_ssl_context():
    """Check default SSL context"""
    print_section("SSL Context")
    
    try:
        context = ssl.create_default_context()
        print(f"✓ Default context created successfully")
        print(f"✓ Check hostname: {context.check_hostname}")
        print(f"✓ Verify mode: {context.verify_mode}")
        
        # Try to get CA certs location
        if hasattr(context, 'ca_certs'):
            print(f"✓ CA certs: {context.ca_certs}")
    except Exception as e:
        print(f"❌ Error creating SSL context: {e}")


def check_system_ca_paths():
    """Check common system CA certificate paths"""
    print_section("System CA Certificate Paths")
    
    common_paths = [
        '/etc/ssl/certs/ca-certificates.crt',  # Debian/Ubuntu
        '/etc/pki/tls/certs/ca-bundle.crt',    # RedHat/CentOS
        '/etc/ssl/ca-bundle.pem',              # OpenSUSE
        '/etc/ssl/cert.pem',                   # OpenBSD
        '/usr/local/share/certs/ca-root-nss.crt',  # FreeBSD
    ]
    
    found_any = False
    for path in common_paths:
        if Path(path).exists():
            size = Path(path).stat().st_size
            print(f"✓ Found: {path} ({size:,} bytes)")
            found_any = True
    
    if not found_any:
        print("ℹ No system CA certificates found at common paths")


def test_https_connection():
    """Test HTTPS connection to Tencent Cloud"""
    print_section("HTTPS Connection Test")
    
    try:
        import urllib.request
        
        url = "https://sts.tencentcloudapi.com"
        print(f"Testing connection to: {url}")
        
        try:
            response = urllib.request.urlopen(url, timeout=5)
            print(f"✓ Connection successful (status: {response.status})")
        except ssl.SSLError as e:
            print(f"❌ SSL Error: {e}")
            print(f"\nℹ This is the SSL issue causing COS CLI to fail")
            return False
        except Exception as e:
            print(f"⚠ Connection error (but not SSL): {e}")
    except ImportError:
        print("⚠ Cannot test - urllib not available")
    
    return True


def check_cos_cli_auth():
    """Check if COS CLI auth module has SSL bypass"""
    print_section("COS CLI SSL Bypass")
    
    try:
        # Navigate up from cos/tools/diagnose_ssl.py to cos/auth.py
        auth_file = Path(__file__).parent.parent / 'auth.py'
        
        if not auth_file.exists():
            # Try alternative path from current working directory
            auth_file = Path.cwd() / 'cos' / 'auth.py'
        
        if auth_file.exists():
            content = auth_file.read_text()
            
            if 'patched_request' in content:
                print("✓ SSL bypass code found in cos/auth.py")
                print("✓ COS CLI should handle SSL issues automatically")
            else:
                print("❌ SSL bypass code NOT found")
                print("⚠ You may need to update COS CLI:")
                print("   git pull origin main")
                print("   pip install -e . --force-reinstall")
        else:
            print("⚠ Cannot locate cos/auth.py")
            print(f"   Looked in: {auth_file}")
    except Exception as e:
        print(f"⚠ Error checking auth module: {e}")


def print_recommendations():
    """Print recommendations based on findings"""
    print_header("Recommendations")
    
    print("""
If you're experiencing SSL certificate errors:

1. Ensure COS CLI is up to date:
   git pull origin main
   pip install -e . --force-reinstall --no-cache-dir

2. If still failing, set environment variables:
   export REQUESTS_CA_BUNDLE=""
   export SSL_CERT_FILE=""
   export CURL_CA_BUNDLE=""

3. For production use, get your corporate CA certificate:
   - Contact your IT department
   - Install it system-wide or use REQUESTS_CA_BUNDLE
   
4. See full documentation:
   docs/SSL_TROUBLESHOOTING.md
""")


def main():
    print_header("COS CLI SSL Diagnostic Tool")
    
    print(f"\nPython version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print(f"Working directory: {os.getcwd()}")
    
    check_environment_variables()
    check_certifi()
    check_ssl_context()
    check_system_ca_paths()
    check_cos_cli_auth()
    
    print("\n")
    ssl_ok = test_https_connection()
    
    if not ssl_ok:
        print_recommendations()
    else:
        print_header("Status: ✓ All Good!")
        print("\nNo SSL issues detected. COS CLI should work correctly.")


if __name__ == '__main__':
    main()
