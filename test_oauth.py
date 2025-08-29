from app import create_app
import os

print("Testing OAuth configuration...")
print(f"Before app creation - OAUTHLIB_INSECURE_TRANSPORT: {os.getenv('OAUTHLIB_INSECURE_TRANSPORT')}")

app = create_app()

print(f"After app creation - OAUTHLIB_INSECURE_TRANSPORT: {os.getenv('OAUTHLIB_INSECURE_TRANSPORT')}")
print(f"FLASK_ENV: {os.getenv('FLASK_ENV')}")
print(f"FLASK_DEBUG: {os.getenv('FLASK_DEBUG')}")

with app.app_context():
    print(f"In app context - OAUTHLIB_INSECURE_TRANSPORT: {os.getenv('OAUTHLIB_INSECURE_TRANSPORT')}")
    print(f"App config FLASK_ENV: {app.config.get('FLASK_ENV')}")
    print(f"App config FLASK_DEBUG: {app.config.get('FLASK_DEBUG')}")
