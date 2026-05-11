import argparse
import json

from google_auth_oauthlib.flow import InstalledAppFlow


SCOPES = ["https://www.googleapis.com/auth/drive"]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate Google Drive OAuth refresh token for Railway secrets."
    )
    parser.add_argument(
        "client_secrets",
        help="Path to OAuth client JSON downloaded from Google Cloud Console.",
    )
    parser.add_argument(
        "--host",
        default="localhost",
        help="Local callback host for the OAuth flow.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=0,
        help="Local callback port. Use 0 to choose a free port.",
    )
    args = parser.parse_args()

    flow = InstalledAppFlow.from_client_secrets_file(args.client_secrets, SCOPES)
    creds = flow.run_local_server(
        host=args.host,
        port=args.port,
        access_type="offline",
        prompt="consent",
        include_granted_scopes="true",
    )

    output = {
        "DRIVE_AUTH_MODE": "oauth",
        "GOOGLE_DRIVE_OAUTH_CLIENT_ID": creds.client_id,
        "GOOGLE_DRIVE_OAUTH_CLIENT_SECRET": creds.client_secret,
        "GOOGLE_DRIVE_OAUTH_REFRESH_TOKEN": creds.refresh_token,
        "GOOGLE_DRIVE_OAUTH_TOKEN_URI": creds.token_uri,
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
