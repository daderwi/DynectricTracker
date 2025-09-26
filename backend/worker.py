import asyncio
import logging
import sys
import os

# Add the app directory to Python path
sys.path.append('/app')

from app.services.scheduler import scheduler_instance

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Hauptfunktion für den Data Collection Worker"""
    try:
        logger.info("Starte Data Collection Worker...")
        scheduler_instance.start()
        
        # Worker läuft endlos
        while True:
            await asyncio.sleep(60)  # Alle Minute überprüfen
            
    except KeyboardInterrupt:
        logger.info("Data Collection Worker wird beendet...")
        scheduler_instance.stop()
    except Exception as e:
        logger.error(f"Fehler im Data Collection Worker: {e}")
        scheduler_instance.stop()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())