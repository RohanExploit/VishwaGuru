# Modular routers for VishwaGuru Backend

# Fix for googletrans compatibility with newer httpcore (Issue #290)
# This monkeypatch must happen before any imports of googletrans or httpx
try:
    import httpcore
    if not hasattr(httpcore, "SyncHTTPTransport"):
        httpcore.SyncHTTPTransport = object
except ImportError:
    pass
