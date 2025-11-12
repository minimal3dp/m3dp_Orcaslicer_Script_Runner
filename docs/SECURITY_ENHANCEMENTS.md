# Security Enhancements

## Overview

This document describes the security enhancements implemented for the BrickLayers web application to protect against common web vulnerabilities and abuse patterns.

## Table of Contents

1. [Rate Limiting](#rate-limiting)
2. [Request Size Limits](#request-size-limits)
3. [File Content Scanning](#file-content-scanning)
4. [API Key Authentication](#api-key-authentication)
5. [Security Headers](#security-headers)
6. [Configuration](#configuration)
7. [Monitoring](#monitoring)

---

## Rate Limiting

### Implementation

Rate limiting prevents abuse by limiting the number of requests from a single IP address within a time window.

**Library**: `slowapi` (FastAPI-compatible rate limiting)

**Limits Applied**:
- **Upload endpoint**: 10 requests per minute per IP
- **Status endpoint**: 30 requests per minute per IP
- **Download endpoint**: 20 requests per minute per IP
- **Cancel endpoint**: 15 requests per minute per IP
- **Global limit**: 100 requests per minute per IP across all endpoints

### Configuration

Environment variables:
```bash
# Rate limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_UPLOAD=10/minute
RATE_LIMIT_STATUS=30/minute
RATE_LIMIT_DOWNLOAD=20/minute
RATE_LIMIT_CANCEL=15/minute
RATE_LIMIT_GLOBAL=100/minute
```

### Response

When rate limit is exceeded:
```json
{
  "type": "https://example.com/errors/rate-limit",
  "title": "Rate Limit Exceeded",
  "status": 429,
  "detail": "Too many requests. Please try again later.",
  "instance": "/upload"
}
```

Headers included:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining in current window
- `X-RateLimit-Reset`: Unix timestamp when limit resets
- `Retry-After`: Seconds to wait before retrying

### Best Practices

1. **Behind Proxy**: Configure `FORWARDED_ALLOW_IPS` to trust proxy headers
2. **Redis Backend**: Use Redis for distributed rate limiting (multi-instance deployments)
3. **Whitelist IPs**: Exempt trusted IPs from rate limiting

---

## Request Size Limits

### Implementation

Request size limits prevent denial-of-service attacks from oversized requests.

**Middleware**: Custom `RequestSizeLimitMiddleware`

**Limits**:
- **Headers**: 16 KB (protects against header-based attacks)
- **Body**: Configurable per endpoint (default 100 MB for uploads)
- **Total Request**: Header + body size validation

### Configuration

```bash
# Request size limits
MAX_HEADER_SIZE_KB=16
MAX_REQUEST_BODY_MB=100
REQUEST_SIZE_LIMIT_ENABLED=true
```

### Response

When request is too large:
```json
{
  "type": "https://example.com/errors/payload-too-large",
  "title": "Request Too Large",
  "status": 413,
  "detail": "Request exceeds maximum allowed size of 100 MB",
  "instance": "/upload"
}
```

### How It Works

1. **Early Detection**: Validates `Content-Length` header before reading body
2. **Streaming Protection**: Tracks bytes read during streaming upload
3. **Incremental Checks**: Aborts early if size limit exceeded
4. **Memory Safe**: Prevents memory exhaustion attacks

---

## File Content Scanning

### Implementation

File content scanning detects malicious patterns in uploaded G-code files.

**Approach**: Pattern-based scanning (no external dependencies)

**Detections**:
1. **Shell Commands**: Detects embedded shell command injection attempts
2. **Path Traversal**: Detects attempts to write outside allowed directories
3. **Suspicious Comments**: Detects encoded payloads or obfuscated code
4. **Firmware Commands**: Detects dangerous firmware commands (M110, M503, etc.)
5. **Script Injection**: Detects embedded scripts (Python, JavaScript, etc.)

### Configuration

```bash
# File content scanning
FILE_SCANNING_ENABLED=true
FILE_SCANNING_STRICT_MODE=false  # If true, reject on any suspicion
ALLOWED_GCODE_EXTENSIONS=.gcode,.gco,.g
```

### Scan Results

**Safe File**: Processing continues normally

**Suspicious File**:
```json
{
  "type": "https://example.com/errors/validation-failed",
  "title": "File Validation Failed",
  "status": 400,
  "detail": "Suspicious content detected: Potential shell command injection",
  "instance": "/upload"
}
```

### Patterns Detected

```python
SUSPICIOUS_PATTERNS = [
    # Shell commands
    r'\$\(.*\)',           # Command substitution
    r'`.*`',               # Backtick execution
    r';\s*(?:rm|wget|curl|nc|bash|sh)\s',  # Chained commands
    
    # Path traversal
    r'\.\.[/\\]',          # Directory traversal
    r'(?:C|D|E):[/\\]',    # Absolute Windows paths
    r'/etc/|/usr/|/var/',  # Absolute Unix paths
    
    # Script injection
    r'<script',            # JavaScript
    r'exec\(',             # Python exec
    r'eval\(',             # Eval functions
    
    # Dangerous G-code
    r'M110\s',             # Reset line numbers (potential confusion)
    r'M503\s',             # Report settings (info leak)
    r'M540\s',             # MAC address (network config)
]
```

### False Positives

To minimize false positives:
- **Context-Aware**: Checks if patterns are in comments vs. actual G-code
- **Whitelist**: Common legitimate patterns are excluded
- **Strict Mode**: Only enable in high-security environments

---

## API Key Authentication

### Implementation

Optional API key authentication for public deployments.

**Approach**: Header-based API keys with configurable requirement

**Security**:
- Keys are hashed (SHA-256) and stored securely
- Rate limits are per-key instead of per-IP when authenticated
- Keys can be revoked without affecting other users

### Configuration

```bash
# API authentication
API_AUTH_ENABLED=false           # Enable/disable authentication
API_AUTH_REQUIRED=false          # If true, all requests must have valid key
API_KEYS=key1:hash1,key2:hash2   # Comma-separated key:hash pairs
API_KEY_HEADER=X-API-Key         # Header name for API key
```

### Usage

**Request with API Key**:
```bash
curl -X POST "http://localhost:8000/upload" \
  -H "X-API-Key: your-api-key-here" \
  -F "file=@model.gcode" \
  -F "start_at_layer=0" \
  -F "extrusion_multiplier=1.0"
```

**Response without valid key** (when required):
```json
{
  "type": "https://example.com/errors/unauthorized",
  "title": "Unauthorized",
  "status": 401,
  "detail": "Valid API key required. Provide key in X-API-Key header.",
  "instance": "/upload"
}
```

### Key Management

**Generate API Key**:
```python
import secrets
import hashlib

# Generate a secure random key
api_key = secrets.token_urlsafe(32)
print(f"API Key: {api_key}")

# Hash for storage
key_hash = hashlib.sha256(api_key.encode()).hexdigest()
print(f"Hash (store this): {key_hash}")
```

**Add to Environment**:
```bash
# .env file
API_KEYS=user1:abc123hash,user2:def456hash
```

### Best Practices

1. **Generate Strong Keys**: Use `secrets.token_urlsafe(32)` or longer
2. **Store Hashes Only**: Never store plaintext keys
3. **Rotate Regularly**: Change keys periodically
4. **Audit Usage**: Log API key usage for security monitoring
5. **Revoke Compromised Keys**: Remove from API_KEYS immediately

---

## Security Headers

### Implementation

Security headers protect against common web vulnerabilities.

**Middleware**: Custom `SecurityHeadersMiddleware`

**Headers Added**:

```http
# Prevent clickjacking
X-Frame-Options: DENY

# Prevent MIME sniffing
X-Content-Type-Options: nosniff

# Enable browser XSS protection
X-XSS-Protection: 1; mode=block

# Referrer policy
Referrer-Policy: strict-origin-when-cross-origin

# Content Security Policy
Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:;

# Permissions policy
Permissions-Policy: geolocation=(), microphone=(), camera=()

# Strict transport security (HTTPS only)
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

### Configuration

```bash
# Security headers
SECURITY_HEADERS_ENABLED=true
HSTS_ENABLED=true              # Require HTTPS
HSTS_MAX_AGE=31536000          # Seconds (1 year)
CSP_ENABLED=true               # Content Security Policy
```

### Testing

**Check Headers**:
```bash
curl -I http://localhost:8000/health
```

**Expected Output**:
```
HTTP/1.1 200 OK
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
...
```

---

## Configuration

### Complete Security Configuration

Create `.env` file with security settings:

```bash
# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_UPLOAD=10/minute
RATE_LIMIT_STATUS=30/minute
RATE_LIMIT_DOWNLOAD=20/minute
RATE_LIMIT_CANCEL=15/minute
RATE_LIMIT_GLOBAL=100/minute

# Request Size Limits
MAX_HEADER_SIZE_KB=16
MAX_REQUEST_BODY_MB=100
REQUEST_SIZE_LIMIT_ENABLED=true

# File Scanning
FILE_SCANNING_ENABLED=true
FILE_SCANNING_STRICT_MODE=false
ALLOWED_GCODE_EXTENSIONS=.gcode,.gco,.g

# API Authentication (optional)
API_AUTH_ENABLED=false
API_AUTH_REQUIRED=false
API_KEYS=
API_KEY_HEADER=X-API-Key

# Security Headers
SECURITY_HEADERS_ENABLED=true
HSTS_ENABLED=false  # Set true in production with HTTPS
HSTS_MAX_AGE=31536000
CSP_ENABLED=true

# Proxy Configuration (if behind reverse proxy)
FORWARDED_ALLOW_IPS=*
PROXY_HEADERS_ENABLED=true
```

### Production Recommendations

1. **Enable All Protections**: Set all `*_ENABLED` to `true`
2. **Tune Rate Limits**: Adjust based on expected traffic patterns
3. **Enable HSTS**: Only after confirming HTTPS works
4. **API Keys**: Required for public deployments
5. **Strict Mode**: Enable file scanning strict mode for high-security environments
6. **Monitoring**: Enable metrics and alerting for security events

---

## Monitoring

### Security Metrics

Prometheus metrics for security events:

```python
# Rate limit hits
bricklayers_rate_limit_exceeded_total{endpoint="/upload"}

# Request size rejections
bricklayers_request_size_rejected_total

# File scanning detections
bricklayers_file_scan_suspicious_total{pattern="shell_command"}

# Authentication failures
bricklayers_auth_failures_total{reason="invalid_key"}
```

### Structured Logging

All security events are logged with context:

```json
{
  "timestamp": "2025-11-11T10:30:00Z",
  "level": "WARNING",
  "logger": "app.middleware.rate_limit",
  "message": "Rate limit exceeded",
  "request_id": "req-abc-123",
  "ip_address": "192.168.1.100",
  "endpoint": "/upload",
  "limit": "10/minute",
  "exceeded_by": 3
}
```

### Alerting

Recommended alerts:

1. **Rate Limit Abuse**: Alert if single IP exceeds limits repeatedly
2. **File Scan Detections**: Alert on suspicious file patterns
3. **Authentication Failures**: Alert on repeated failed auth attempts
4. **Request Size Attacks**: Alert on multiple oversized requests

---

## Security Checklist

### Pre-Deployment

- [ ] Enable rate limiting with appropriate limits
- [ ] Configure request size limits based on expected file sizes
- [ ] Enable file content scanning
- [ ] Generate and configure API keys (if public)
- [ ] Enable security headers
- [ ] Configure HSTS (HTTPS required)
- [ ] Set up proxy configuration if behind load balancer
- [ ] Review and customize CSP headers
- [ ] Test all security features in staging

### Post-Deployment

- [ ] Monitor rate limit metrics
- [ ] Review security logs daily
- [ ] Set up alerting for security events
- [ ] Rotate API keys regularly
- [ ] Update suspicious pattern list based on detections
- [ ] Perform security audit quarterly
- [ ] Keep dependencies updated

---

## Troubleshooting

### Rate Limit Issues

**Problem**: Legitimate users being rate-limited

**Solutions**:
1. Increase rate limits for specific endpoints
2. Implement API key authentication to bypass IP limits
3. Whitelist trusted IPs
4. Use Redis for more accurate distributed counting

### File Scanning False Positives

**Problem**: Valid G-code files being rejected

**Solutions**:
1. Disable strict mode: `FILE_SCANNING_STRICT_MODE=false`
2. Review pattern matches in logs
3. Add pattern to whitelist
4. Submit issue with sample file for analysis

### HSTS Issues

**Problem**: Browser refuses non-HTTPS connections

**Solutions**:
1. Ensure HTTPS is properly configured
2. Clear HSTS cache in browser settings
3. Only enable HSTS in production with valid certificates
4. Use shorter `HSTS_MAX_AGE` during testing

### API Key Not Working

**Problem**: Valid API key rejected

**Solutions**:
1. Verify key hash is correct in `API_KEYS`
2. Check header name matches `API_KEY_HEADER`
3. Ensure no whitespace in key or hash
4. Verify `API_AUTH_ENABLED=true`
5. Check logs for specific error messages

---

## Related Documentation

- [BACKGROUND_JOBS.md](./BACKGROUND_JOBS.md) - Job management and cancellation
- [METRICS.md](./METRICS.md) - Prometheus metrics and monitoring
- [STRUCTURED_LOGGING.md](./STRUCTURED_LOGGING.md) - Logging infrastructure
- [FASTAPI_STRUCTURE.md](./FASTAPI_STRUCTURE.md) - Application architecture

---

**Last Updated**: 2025-11-11  
**Version**: 1.1.7  
**Security Level**: Production-Ready
