import asyncio
import logging
from datetime import datetime, timedelta
from typing import List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from ..config import settings
from ..database import SessionLocal
from ..data_collectors import ENTSOECollector, AwattarCollector, TibberCollector
from ..models import Provider

logger = logging.getLogger(__name__)


class DataCollectionScheduler:
    """Scheduler für automatisierte Datensammlung"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.collectors = {}
        self.is_running = False
    
    def initialize_collectors(self):
        """Initialisiere alle verfügbaren Datensammler"""
        # ENTSO-E Collector
        if settings.entso_e_api_key:
            self.collectors['ENTSO-E'] = ENTSOECollector(settings.entso_e_api_key)
            logger.info("ENTSO-E Collector initialisiert")
        
        # aWATTar Collector (braucht keinen API Key)
        self.collectors['aWATTar'] = AwattarCollector()
        logger.info("aWATTar Collector initialisiert")
        
        # Tibber Collector
        if settings.tibber_api_key:
            self.collectors['Tibber'] = TibberCollector(settings.tibber_api_key)
            logger.info("Tibber Collector initialisiert")
        
        logger.info(f"Insgesamt {len(self.collectors)} Collectors initialisiert")
    
    def start(self):
        """Starte den Scheduler"""
        if self.is_running:
            logger.warning("Scheduler läuft bereits")
            return
        
        try:
            self.initialize_collectors()
            
            # Hauptsammlung alle 15 Minuten
            self.scheduler.add_job(
                self.collect_all_data,
                trigger=IntervalTrigger(seconds=settings.data_collection_interval),
                id='main_collection',
                name='Hauptdatensammlung',
                replace_existing=True
            )
            
            # Stündliche Sammlung für Day-Ahead Preise
            self.scheduler.add_job(
                self.collect_day_ahead_data,
                trigger='cron',
                minute=5,  # 5 Minuten nach jeder Stunde
                id='day_ahead_collection',
                name='Day-Ahead Preissammlung',
                replace_existing=True
            )
            
            # Tägliche Bereinigung alter Daten
            self.scheduler.add_job(
                self.cleanup_old_data,
                trigger='cron',
                hour=2,  # 2:00 Uhr morgens
                minute=0,
                id='data_cleanup',
                name='Datenbereinigung',
                replace_existing=True
            )
            
            # Stündliche Gesundheitsprüfung
            self.scheduler.add_job(
                self.health_check,
                trigger='cron',
                minute=30,  # 30 Minuten nach jeder Stunde
                id='health_check',
                name='Gesundheitsprüfung',
                replace_existing=True
            )
            
            self.scheduler.start()
            self.is_running = True
            logger.info("Data Collection Scheduler gestartet")
            
            # Initiale Datensammlung
            asyncio.create_task(self.initial_data_collection())
            
        except Exception as e:
            logger.error(f"Fehler beim Starten des Schedulers: {e}")
            raise
    
    def stop(self):
        """Stoppe den Scheduler"""
        if not self.is_running:
            return
        
        try:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Data Collection Scheduler gestoppt")
        except Exception as e:
            logger.error(f"Fehler beim Stoppen des Schedulers: {e}")
    
    async def initial_data_collection(self):
        """Erste Datensammlung beim Start"""
        logger.info("Starte initiale Datensammlung...")
        await asyncio.sleep(5)  # Kurz warten nach dem Start
        await self.collect_all_data()
    
    async def collect_all_data(self):
        """Sammle Daten von allen verfügbaren Quellen"""
        logger.info("Starte Datensammlung von allen Quellen")
        
        # Zeitfenster: letzte 2 Stunden bis in 48 Stunden
        start_time = datetime.now() - timedelta(hours=2)
        end_time = datetime.now() + timedelta(hours=48)
        
        db = SessionLocal()
        total_collected = 0
        
        try:
            # Parallel alle Collector ausführen
            tasks = []
            for collector_name, collector in self.collectors.items():
                tasks.append(self._collect_from_source(collector, db, start_time, end_time))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Ergebnisse auswerten
            for i, result in enumerate(results):
                collector_name = list(self.collectors.keys())[i]
                if isinstance(result, Exception):
                    logger.error(f"Fehler bei {collector_name}: {result}")
                else:
                    total_collected += result
                    logger.info(f"{collector_name}: {result} Datensätze gesammelt")
            
            logger.info(f"Datensammlung abgeschlossen: {total_collected} Datensätze insgesamt")
            
        except Exception as e:
            logger.error(f"Fehler bei der Datensammlung: {e}")
        finally:
            db.close()
    
    async def _collect_from_source(self, collector, db: Session, start_time: datetime, end_time: datetime) -> int:
        """Sammle Daten von einer spezifischen Quelle"""
        try:
            return await collector.collect_and_store(db, start_time, end_time)
        except Exception as e:
            logger.error(f"Fehler bei Collector {collector.provider_name}: {e}")
            return 0
    
    async def collect_day_ahead_data(self):
        """Sammle spezifisch Day-Ahead Preise (täglich um ca. 14:00 verfügbar)"""
        logger.info("Sammle Day-Ahead Preise")
        
        # Morgen und übermorgen
        tomorrow = (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_after = tomorrow + timedelta(days=1)
        
        db = SessionLocal()
        
        try:
            # Nur ENTSO-E für Day-Ahead Preise
            if 'ENTSO-E' in self.collectors:
                collector = self.collectors['ENTSO-E']
                collected = await collector.collect_and_store(db, tomorrow, day_after)
                logger.info(f"Day-Ahead Sammlung: {collected} Datensätze")
            
        except Exception as e:
            logger.error(f"Fehler bei Day-Ahead Sammlung: {e}")
        finally:
            db.close()
    
    async def cleanup_old_data(self):
        """Bereinige alte Daten basierend auf Retention Policy"""
        logger.info("Starte Datenbereinigung")
        
        cutoff_date = datetime.now() - timedelta(days=settings.retention_days)
        db = SessionLocal()
        
        try:
            from ..models import ElectricPrice, DataCollectionLog
            
            # Alte Preisdaten löschen
            deleted_prices = db.query(ElectricPrice).filter(
                ElectricPrice.timestamp < cutoff_date
            ).delete()
            
            # Alte Logs löschen (nur ältere als 90 Tage)
            log_cutoff = datetime.now() - timedelta(days=90)
            deleted_logs = db.query(DataCollectionLog).filter(
                DataCollectionLog.collection_time < log_cutoff
            ).delete()
            
            db.commit()
            
            logger.info(f"Datenbereinigung abgeschlossen: {deleted_prices} Preisdaten und {deleted_logs} Logs gelöscht")
            
        except Exception as e:
            logger.error(f"Fehler bei der Datenbereinigung: {e}")
            db.rollback()
        finally:
            db.close()
    
    async def health_check(self):
        """Überprüfe Gesundheit der Datensammlung"""
        logger.info("Führe Gesundheitsprüfung durch")
        
        db = SessionLocal()
        
        try:
            from ..models import DataCollectionLog, Provider
            
            # Prüfe letzte Datensammlung pro Provider
            one_hour_ago = datetime.now() - timedelta(hours=1)
            
            providers = db.query(Provider).filter(Provider.is_active == True).all()
            
            for provider in providers:
                latest_log = db.query(DataCollectionLog).filter(
                    DataCollectionLog.provider_id == provider.id,
                    DataCollectionLog.collection_time >= one_hour_ago
                ).order_by(DataCollectionLog.collection_time.desc()).first()
                
                if not latest_log:
                    logger.warning(f"Keine aktuellen Daten für {provider.display_name}")
                elif latest_log.status == "error":
                    logger.warning(f"Sammelfehler bei {provider.display_name}: {latest_log.error_message}")
                else:
                    logger.debug(f"{provider.display_name}: OK ({latest_log.records_collected} Datensätze)")
            
        except Exception as e:
            logger.error(f"Fehler bei der Gesundheitsprüfung: {e}")
        finally:
            db.close()
    
    def get_status(self) -> dict:
        """Gebe aktuellen Status des Schedulers zurück"""
        if not self.is_running:
            return {"status": "stopped", "jobs": []}
        
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })
        
        return {
            "status": "running",
            "collectors": list(self.collectors.keys()),
            "jobs": jobs
        }


# Globale Scheduler-Instanz
scheduler_instance = DataCollectionScheduler()