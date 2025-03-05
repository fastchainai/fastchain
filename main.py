"""Main application entry point."""
import sys
import socket
import logging
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def is_port_in_use(port: int) -> bool:
    """Check if a port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('0.0.0.0', port))
            logger.debug(f"Port {port} is available")
            return False
        except socket.error as e:
            logger.error(f"Port {port} is in use: {str(e)}")
            return True

if __name__ == "__main__":
    try:
        PORT = 5000
        logger.info(f"Starting FastAPI server on port {PORT}")

        # Check if port is available
        if is_port_in_use(PORT):
            logger.error(f"Port {PORT} is already in use. Please free up the port and try again.")
            sys.exit(1)

        # Set uvicorn logging config
        log_config = uvicorn.config.LOGGING_CONFIG
        log_config["formatters"]["default"]["fmt"] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        log_config["loggers"]["uvicorn"]["level"] = "DEBUG"
        log_config["loggers"]["uvicorn.error"]["level"] = "DEBUG"
        log_config["loggers"]["uvicorn.access"]["level"] = "DEBUG"

        logger.info("Starting uvicorn server with updated logging configuration")

        uvicorn.run(
            "src.api.main_router:app",  # Using the correct app instance
            host="0.0.0.0",
            port=PORT,
            reload=True,
            log_level="debug",
            log_config=log_config
        )
    except ImportError as e:
        logger.error(f"Failed to import required modules: {e}", exc_info=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to start server: {e}", exc_info=True)
        sys.exit(1)