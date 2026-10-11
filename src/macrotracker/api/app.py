
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from macrotracker.api.routes import router
from macrotracker.config.source import get_settings, load_indicator_list
from macrotracker.database.create_db import Database
from macrotracker.database.syncdb import sync
from macrotracker.utils.logger import setup_logger

logger = setup_logger(__name__)

def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # load all settings and indicator list to app state
        base_cfg = get_settings()
        indicators = load_indicator_list(base_cfg.indicator_list)
        storage = Database(base_cfg.database_path)
        app.state.base_cfg = base_cfg # Store the base configuration in the app state
        app.state.storage = storage # path database
        app.state.indicators = indicators # list of indicators
        app.state.sync_done = False
        app.state.sync_error = None 
        # peform sync of database
        try:
            await asyncio.to_thread(sync, storage, indicators)
            app.state.sync_done = True
        except Exception as e:
            logger.exception('Database Sync Failed')
            app.state.sync_error = str(e)
            app.state.sync_done = False
        yield
    app = FastAPI(lifespan=lifespan)
    app.include_router(router)
    return app