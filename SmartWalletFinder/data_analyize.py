import pandas as pd

# 示例数据，假设代币符号为 MEME
data = [
    {'wallet_address': '0x1', 'tx_time': '2023-09-01 12:00:00', 'token0_symbol': 'ETH', 'token1_symbol': 'MEME',
     'token0_amount': 1.0, 'token1_amount': 100000.0, 'direction': 1},
    {'wallet_address': '0x1', 'tx_time': '2023-09-05 15:30:00', 'token0_symbol': 'MEME', 'token1_symbol': 'ETH',
     'token0_amount': 110000.0, 'token1_amount': 2.0, 'direction': 0},
    {'wallet_address': '0x2', 'tx_time': '2023-09-03 18:45:00', 'token0_symbol': 'ETH', 'token1_symbol': 'MEME',
     'token0_amount': 2.0, 'token1_amount': 200000.0, 'direction': 1},
    {'wallet_address': '0x2', 'tx_time': '2023-09-07 09:20:00', 'token0_symbol': 'MEME', 'token1_symbol': 'ETH',
     'token0_amount': 220000.0, 'token1_amount': 4.5, 'direction': 0},
    {'wallet_address': '0x1', 'tx_time': '2023-09-10 12:30:00', 'token0_symbol': 'ETH', 'token1_symbol': 'MEME',
     'token0_amount': 1.5, 'token1_amount': 105000.0, 'direction': 1},
    {'wallet_address': '0x3', 'tx_time': '2023-09-04 17:15:00', 'token0_symbol': 'ETH', 'token1_symbol': 'MEME',
     'token0_amount': 0.5, 'token1_amount': 50000.0, 'direction': 1},
    {'wallet_address': '0x3', 'tx_time': '2023-09-12 09:00:00', 'token0_symbol': 'MEME', 'token1_symbol': 'ETH',
     'token0_amount': 60000.0, 'token1_amount': 1.2, 'direction': 0},
]

# 将数据转换为 DataFrame
df = pd.DataFrame(data)

# 将交易时间转换为datetime格式
df['tx_time'] = pd.to_datetime(df['tx_time'])

# 按钱包地址和交易时间排序
df = df.sort_values(by=['wallet_address', 'tx_time'])


# 定义利润计算逻辑，确保利润只计算到最后一次卖出MEME的交易
def calculate_eth_profit(wallet_df):
    # 找到最后一次卖出MEME（direction == 0）的交易索引
    last_sell_index = wallet_df[wallet_df['direction'] == 0].last_valid_index()

    # 截取到最后一次卖出为止的交易记录
    truncated_wallet_df = wallet_df.loc[:last_sell_index]

    eth_profit = 0.0

    # 累计计算 ETH 利润
    for _, row in truncated_wallet_df.iterrows():
        if row['token0_symbol'] == 'ETH':
            eth_profit -= row['token0_amount']  # 买入ETH时，减少ETH
        elif row['token1_symbol'] == 'ETH':
            eth_profit += row['token1_amount']  # 卖出ETH时，增加ETH

    return eth_profit


# 按钱包地址分组并计算利润
wallet_profits = df.groupby('wallet_address').apply(calculate_eth_profit).reset_index()
wallet_profits.columns = ['wallet_address', 'eth_profit']

# 按利润排序，找出利润最高的钱包
wallet_profits = wallet_profits.sort_values(by='eth_profit', ascending=False)

# 打印结果
print(wallet_profits)
