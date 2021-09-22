# Globals related to db connections etc.
from conn.mysql import MySQLPool
from logger import error
from config import conf
import traceback
import aioredis

__slots__ = ("sql", "loop")

sql = MySQLPool()
redis = aioredis.Redis()

# Startup tasks.
async def connect_sql() -> bool:
    """Connects the MySQL pool to the server.
    
    Returns bool corresponding to whether it was successful.
    """

    try:
        await sql.connect(
            host= conf.sql_host,
            user= conf.sql_user,
            database= conf.sql_db,
            password= conf.sql_password,
        )
        return True
    except Exception:
        error(f"There has been an exception connecting to the MySQL server!\n" 
              + traceback.format_exc())
        return False

async def connect_redis() -> bool:
    """Connects the Redis pool to the server.
    
    Returns bool corresponding to whether it was successful.
    """

    try:
        global redis
        redis = await aioredis.create_redis_pool("redis://localhost")
        return True
    except Exception:
        error(f"There has been an exception connecting to the Redis database!\n" 
              + traceback.format_exc())
        return False
