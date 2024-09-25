from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from psycopg2.extras import RealDictCursor
import sqlalchemy
from db.models import Measure, database, metadata, engine
from routes import *


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not database.is_connected:
        await database.connect()  

    tables_exist = sqlalchemy.inspect(engine).has_table(Measure.get_name)
    if not tables_exist:
        metadata.create_all(engine)
        
    yield
    
    if database.is_connected:
        await database.disconnect()


app = FastAPI(title='MedidasPR')

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
