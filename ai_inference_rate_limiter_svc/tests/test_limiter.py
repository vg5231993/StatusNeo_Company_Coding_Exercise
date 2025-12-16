import pytest
from unittest.mock import MagicMock
from redis.exceptions import RedisError
from app.limiter import DistributedRateLimiter
from app.config import settings

MOCK_LIMIT = 5

# test Fixture for Mock Data
@pytest.fixture
def mock_limiter(mocker):
    mocker.patch('app.limiter.Redis', autospec=True)
    limiter = DistributedRateLimiter()
    limiter.redis_client = MagicMock()
    limiter.lua_script_sha = "MOCK_SHA" 
    return limiter

def test_limiter_init_loads_script_and_pings(mocker):
    """Tests the initializer tries to connect and load the script."""
    mock_redis_class = mocker.patch('app.limiter.Redis')
    mocker.patch('builtins.open', mocker.mock_open(read_data='lua script content'))
    mock_redis_class.return_value.script_load.return_value = "TEST_SHA"

    limiter = DistributedRateLimiter()
    
    assert limiter.lua_script_sha == "TEST_SHA"
    mock_redis_class.return_value.ping.assert_called_once()
    
def test_allow_success(mock_limiter):
    """Test case checks return 1"""
    mock_limiter.redis_client.evalsha.return_value = 1
    
    result = mock_limiter.allow("user_a", "model_x", MOCK_LIMIT)
    
    assert result is True
    
    mock_limiter.redis_client.evalsha.assert_called_once()
    args, _ = mock_limiter.redis_client.evalsha.call_args
    
    assert args[2] == "rl:user_a:model_x"
    assert args[5] == MOCK_LIMIT

def test_allow_rejection(mock_limiter):
    """Test case condition to check returns 0"""
    mock_limiter.redis_client.evalsha.return_value = 0
    
    result = mock_limiter.allow("user_b", "model_y", MOCK_LIMIT)
    
    assert result is False

def test_allow_redis_failure_fails_open(mock_limiter):
    """
    Test checks the request is ALLOWED to prevent service disruption.
    """
    mock_limiter.redis_client.evalsha.side_effect = RedisError("Redis Failure")
    result = mock_limiter.allow("user_c", "model_z", MOCK_LIMIT)
    
    assert result is True