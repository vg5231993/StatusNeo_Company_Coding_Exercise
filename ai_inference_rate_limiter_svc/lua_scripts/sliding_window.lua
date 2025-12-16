-- Implements the Sliding Window Log Rate Limiter using Redis Sorted Sets (ZSET).
-- Executes cleanup, counting, and insertion as a single atomic transaction.

-- KEYS[1]: Redis ZSET key 
-- ARGV[1]: current Unix timestamp in milliseconds
-- ARGV[2]: starting of the time window i.e. current_time - WINDOW_DURATION
-- ARGV[3]: maximum request limit e.g. 100
-- ARGV[4]: expiration TTL for the key e.g. 3660 seconds

local current_time = tonumber(ARGV[1])
local window_start_time = tonumber(ARGV[2])
local max_limit = tonumber(ARGV[3])
local key_ttl = tonumber(ARGV[4])

-- the below code is the "sliding" part of the window. it clean up the old logs and removes the members
redis.call('ZREMRANGEBYSCORE', KEYS[1], 0, window_start_time)

local current_count = redis.call('ZCARD', KEYS[1])

-- validation - Checking Limits 
if current_count < max_limit then
    redis.call('ZADD', KEYS[1], current_time, current_time)
    redis.call('EXPIRE', KEYS[1], key_ttl) 
    
    return 1
else
    return 0
end