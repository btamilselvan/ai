import redis


class ResourceRegistry:
    redis_client: redis.Redis

    def setup_redis_client(self, host="localhost", port=6379, db=0, max_connections=10):
        """setup redis client and add to registry"""
        pool = redis.ConnectionPool(
            host=host, port=port, db=db, max_connections=max_connections
        )
        self.redis_client = redis.Redis(connection_pool=pool)
