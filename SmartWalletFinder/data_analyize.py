import pandas as pd


def append_token_swap_data(data, token0_sympol:str, token1_sympol:str):
    # 文件名可以包含代币符号和交易信息汇总
    filename = f"token_swap_{token0_sympol}_{token1_sympol}.csv"
    # 将数据转换为 DataFrame
    df = pd.DataFrame(data)
    # 如果文件已存在，追加写入，不写入表头
    try:
        with open(filename, 'r') as f:
            df.to_csv(filename, mode='a', header=False, index=False)
    except FileNotFoundError:
        # 如果文件不存在，创建文件并写入表头
        df.to_csv(filename, mode='w', header=True, index=False)
    print(f"追加保存 {token0_sympol}/{token1_sympol} 的交易信息到文件: {filename}")
    execute_analyize(df)


def execute_analyize(df):
    # 将交易时间转换为datetime格式
    df['tx_time'] = pd.to_datetime(df['tx_time'])

    # 按钱包地址和交易时间排序
    df = df.sort_values(by=['wallet_address', 'tx_time'])
    # 按钱包地址分组并计算利润
    wallet_profits = df.groupby('wallet_address').apply(calculate_eth_profit).reset_index()
    wallet_profits.columns = ['wallet_address', 'eth_profit']
    # 按利润排序，找出利润最高的钱包
    wallet_profits = wallet_profits.sort_values(by='eth_profit', ascending=False)
    # 打印结果
    print(wallet_profits)

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


