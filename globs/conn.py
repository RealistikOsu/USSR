# Globals related to db connections etc.
from conn.mysql import MySQLPool
from logger import error
from config import conf
import traceback
import uvloop

__slots__ = ("sql", "loop")

sql = MySQLPool()
loop = uvloop.new_event_loop()

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
            loop= loop
        )
        return True
    except Exception:
        tb = traceback.format_exc()
        error(f"There has been an exception connecting to the MySQL server!\n" + tb)
        return False
