from typing import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
import sqlalchemy

from db.models import OrmarConfig, engine, base_ormar_config
from routes import *


def get_lifespan(config: OrmarConfig):
    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        if not config.database.is_connected:
            await config.database.connect()  

        tables_exist = sqlalchemy.inspect(engine).get_table_names()
        if not tables_exist:
            config.metadata.create_all(engine)
            
        yield
        
        if config.database.is_connected:
            await config.database.disconnect()
            
    return lifespan

app = FastAPI(title='MedidasPR', lifespan=get_lifespan(base_ormar_config))

app.include_router(legislator_router)
    
if __name__ == '__main__':
    
    # reload_enabled = True if len(sys.argv) == 2 and sys.argv[1] == 'reload' else False
    import uvicorn
    uvicorn.run(
        'main:app', 
        host='0.0.0.0', 
        port=8000, 
        # reload=True if reload_enabled else False, 
        reload=True, 
    )
