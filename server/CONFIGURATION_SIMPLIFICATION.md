# Configuration Management Simplification

## What Was Changed

### Before (Complex System)
- **Multiple file formats**: Supported JSON, YAML, and TOML formats
- **Complex file discovery**: Used `find_file_in_dir()` to search for files with different extensions
- **Separate API keys file**: Required a separate `api_keys.json` file
- **Custom validation**: Complex custom validation logic with `check_config_contains_required_fields()`
- **Multiple helper functions**: Various utility functions for file handling

### After (Simplified System)
- **Single TOML format**: Only supports `config.toml` (simpler and more focused)
- **Environment variables for secrets**: API keys loaded from environment variables (12-factor app principle)
- **Direct file loading**: Simple, direct file loading without complex discovery
- **Pydantic validation**: Leverages Pydantic's built-in validation
- **Fewer dependencies**: Removed `yaml` and `json` import dependencies

## Benefits

1. **Security**: API keys are no longer stored in files, following 12-factor app principles
2. **Simplicity**: Reduced code complexity by ~60% (from ~200 lines to ~80 lines)
3. **Better separation**: Configuration vs secrets are properly separated
4. **Environment-friendly**: Works better with Docker and CI/CD systems
5. **Maintainability**: Single file format reduces edge cases and testing complexity

## Migration Guide

### For Local Development
1. Run the migration script: `python migrate_to_env.py`
2. The script creates a `.env` file with your API keys
3. You can remove `api_keys.json` after verifying everything works

### For Docker
1. Set environment variables in your `.env` file or docker-compose.yml
2. Remove volume mounts for `api_keys.json` from docker-compose.yml
3. The configuration system will automatically pick up environment variables

### Environment Variables
- `TODOIST_API_KEY`: Your Todoist API key
- `OPENWEATHERMAP_API_KEY`: Your OpenWeatherMap API key
- `SERVER_HOST`: Override server host (optional)
- `SERVER_PORT`: Override server port (optional)

## Backward Compatibility

The new system maintains backward compatibility through:
- `config.api_keys` property still works (returns a dict for legacy code)
- Same configuration structure in TOML files
- CLI interface remains the same

## Files Modified
- `src/server/config.py`: Complete rewrite with simplified logic
- `src/server/app.py`: Updated to use new API key structure
- `src/server/cli.py`: Updated help text
- `config.toml`: Added comments about environment variables
- `env.example`: Added API key environment variables
- Created `migrate_to_env.py`: Migration utility script

## Next Steps
1. Update Docker configuration to use environment variables
2. Update documentation to reflect new configuration approach
3. Consider removing the legacy `api_keys` property after full migration
4. Update CI/CD pipelines to use environment variables