"""
Run the server directly with: python -m server

For development with auto-reload, use:
    fastapi dev server/main.py

For production, use:
    fastapi run server/main.py
"""

if __name__ == "__main__":
    import uvicorn
    from pathlib import Path
    import os
    from server.config import AppConfig
    
    # Load config to get host/port
    config_dir = Path(os.environ.get("CONFIG_DIR", "."))
    config = AppConfig.from_dir(config_dir)
    
    # Run with uvicorn
    uvicorn.run(
        "server.main:app",
        host=str(config.server.host),
        port=config.server.port,
        reload=True
    )
