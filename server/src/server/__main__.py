from server.cli import cli

"""
After pip installing the .whl, run this from the command line:
    nohup server start > ~/uvicorn.log &1>2
"""

if __name__ == "__main__":
    cli()
