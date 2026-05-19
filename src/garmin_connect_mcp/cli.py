"""Command-line entry point for Garmin Connect MCP."""

import sys


def main() -> None:
    """Run the MCP server or a supported subcommand."""
    args = sys.argv[1:]

    if not args:
        from .server import main as server_main

        server_main()
        return

    if args == ["auth"]:
        from .scripts.setup_auth import main as auth_main

        auth_main()
        return

    if args[0] in {"-h", "--help", "help"}:
        print("Usage: garmin-connect-mcp [auth]")
        return

    print(f"Unknown command: {args[0]}", file=sys.stderr)
    print("Usage: garmin-connect-mcp [auth]", file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
