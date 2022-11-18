# ## IHTC compliance

# current django version settings config docs: https://docs.djangoproject.com/en/3.2/ref/settings/

# Set crsf cookie to be secure
CSRF_COOKIE_SECURE = True

# Set session cookie to be secure
SESSION_COOKIE_SECURE = True

# Make browser end session when user closes browser
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Set cookie expiry to 4 hours
SESSION_COOKIE_AGE = 4 * 60 * 60  # 4 hours

# Prevent client side JS from accessing CRSF token
CSRF_COOKIE_HTTPONLY = True

# Prevent client side JS from accessing session cookie (true by default)
SESSION_COOKIE_HTTPONLY = True

# Set content to no sniff
SECURE_CONTENT_TYPE_NOSNIFF = True

# Set anti XSS header
SECURE_BROWSER_XSS_FILTER = True

# Audit log middleware user field
AUDIT_LOG_USER_FIELD = "username"

# Default value for the X-Frame-Options header used by XFrameOptionsMiddleware.
X_FRAME_OPTIONS = "DENY"

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# SecurityMiddleware redirects all non-HTTPS requests
# to HTTPS (except for those URLs matching a
# regular expression listed in SECURE_REDIRECT_EXEMPT
SECURE_SSL_REDIRECT = True

SECURE_HSTS_SECONDS = 0
