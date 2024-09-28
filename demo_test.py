from cachetools import cached, TTLCache

cache = TTLCache(maxsize=100, ttl=300)  # 设置最大缓存条目数和缓存超时时间（秒）

@cached(cache)
def expensive_operation(x, y):
    print("caculate")
    # 计算复杂的操作
    return x * y

# 第一次调用会计算并缓存结果
print(expensive_operation(2, 3))  # 输出: 6

# 第二次调用时直接从缓存中获取结果，而不重新计算
print(expensive_operation(2, 3))  # 输出: 6