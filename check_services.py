"""
Diagnostics script to test PostgreSQL and Redis connections.
Run this to identify which service is refusing connections.
"""

import asyncio
import sys
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

async def test_postgresql():
    """Test PostgreSQL connection"""
    print("\n" + "="*60)
    print("Testing PostgreSQL Connection")
    print("="*60)
    
    database_url = os.getenv("DATABASE_URL")
    print(f"DATABASE_URL: {database_url}")
    
    try:
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy import text
        
        # Create engine
        engine = create_async_engine(database_url, echo=False)
        
        # Test connection
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            value = result.scalar()
            print(f"✅ PostgreSQL connection successful!")
            print(f"   Query result: {value}")
        
        await engine.dispose()
        return True
        
    except ImportError as e:
        print(f"❌ ImportError: {e}")
        print("   Make sure SQLAlchemy and asyncpg are installed:")
        print("   pip install sqlalchemy[asyncio] asyncpg")
        return False
    except Exception as e:
        print(f"❌ PostgreSQL connection failed!")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error message: {e}")
        return False


async def test_redis():
    """Test Redis connection"""
    print("\n" + "="*60)
    print("Testing Redis Connection")
    print("="*60)
    
    redis_url = os.getenv("REDIS_URL")
    print(f"REDIS_URL: {redis_url}")
    
    try:
        import redis.asyncio as redis
        
        # Parse URL to extract host and port
        # Format: redis://localhost:6379/0
        url_parts = redis_url.replace("redis://", "").split("/")
        host_port = url_parts[0]
        if ":" in host_port:
            host, port = host_port.split(":")
            port = int(port)
        else:
            host = host_port
            port = 6379
        
        print(f"   Host: {host}")
        print(f"   Port: {port}")
        
        # Create Redis client
        client = redis.Redis(host=host, port=port, decode_responses=True)
        
        # Test connection with PING
        result = await client.ping()
        print(f"✅ Redis connection successful!")
        print(f"   PING result: {result}")
        
        await client.close()
        return True
        
    except ImportError as e:
        print(f"❌ ImportError: {e}")
        print("   Make sure redis is installed:")
        print("   pip install redis")
        return False
    except Exception as e:
        print(f"❌ Redis connection failed!")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error message: {e}")
        return False


async def main():
    """Run all diagnostics"""
    print("\n" + "="*60)
    print("Rafeeq Service Diagnostics")
    print("="*60)
    
    # Test PostgreSQL
    pg_ok = await test_postgresql()
    
    # Test Redis
    redis_ok = await test_redis()
    
    # Summary
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    print(f"PostgreSQL: {'✅ OK' if pg_ok else '❌ FAILED'}")
    print(f"Redis:      {'✅ OK' if redis_ok else '❌ FAILED'}")
    
    if pg_ok and redis_ok:
        print("\n✅ All services are running correctly!")
        sys.exit(0)
    else:
        print("\n❌ Some services are not accessible. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
