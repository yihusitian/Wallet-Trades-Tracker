import time
from web3 import Web3
from hexbytes import HexBytes
from OnChain import constants as c
from SmartWalletFinder import functions as f


# 连接到以太坊节点 (例如 Infura)
infura_url = 'https://mainnet.infura.io/v3/cf894d2a298148e1b27782472731936e'
web3 = Web3(Web3.HTTPProvider(infura_url))

def processEvent(tx_log):
    print(tx_log)
    # tx_hash = event['transactionHash'].hex()
    # swap_data = tx_log['data']
    # pool_address = tx_log['address']
    # print(f"交易哈希: {tx_hash}")
    # # 获取交易收据
    # tx_receipt = web3.eth.get_transaction_receipt(tx_hash)
    # print("-" * 50)


if __name__ == '__main__':
    # print(functions.getUniswapV2PairAddress(web3, '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', '0xc3D2B3e23855001508e460A6dbE9f9e3116201aF'))
    # print(functions.getUniswapV3PairAddress(web3, '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', '0xc3D2B3e23855001508e460A6dbE9f9e3116201aF'))

    pair_addresses = []
    uniswap_v2_pair_address = f.getUniswapV2PairAddress(web3, '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', '0xc3D2B3e23855001508e460A6dbE9f9e3116201aF')
    uniswap_v3_pair_address = f.getUniswapV3PairAddress(web3, '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', '0xc3D2B3e23855001508e460A6dbE9f9e3116201aF')
    print(uniswap_v2_pair_address)
    if uniswap_v2_pair_address:
        pair_addresses.append(uniswap_v2_pair_address)
    if uniswap_v3_pair_address:
        for v3_pair_address in uniswap_v3_pair_address:
            pair_addresses.append(v3_pair_address)
    print(pair_addresses)

    # 查询某个代币合约的历史事件
    filter_params = {
        # 到最新区块
    'fromBlock': 20819132,  # 过去100000个区块
    'toBlock': 20819132,  # 到最新区块
        # 'fromBlock': web3.eth.block_number - 100,  # 过去100000个区块
        # 'toBlock': web3.eth.block_number,  # 到最新区块
        'address':pair_addresses,
        'topics': [
            [swap_event.hex() for sublist in [swap_events for swap_events in c.SWAPS_HEX.values()] for swap_event in sublist]
        ]  # 可选择特定事件签名，也可以留空
    }
    #
    # 创建过滤器
    history_filter = web3.eth.filter(filter_params)

    # 查询历史事件
    events = history_filter.get_all_entries()
    for event in events:
        # print(f"历史事件: {event}")
        processEvent(event)
    print([item for item in c.SWAPS_HEX.values()])

    # print([swap_event.hex() for sublist in [swap_events for swap_events in c.SWAPS_HEX.values()] for swap_event in sublist])

#
#
# # 检查连接状态
# if web3.is_connected():
#     print("已成功连接到以太坊节点")
# else:
#     print("连接失败")
#
# # 定义聪明钱包地址（可以添加多个地址）
# smart_money_addresses = [
#     web3.to_checksum_address('0x43f708c3f68B5fE2Fe5cf38844b56613c71fc544'),
#     # 添加更多地址
# ]
#
# # Uniswap V2 Router合约地址
# uniswap_v2_router_address = web3.to_checksum_address(
#     '0x54f5044Efd8538C41cCd4bfFb06cf375C9bBb6c4')  # Uniswap V2 Router地址
# # Uniswap V3 Router合约地址
# uniswap_v3_router_address = web3.to_checksum_address(
#     '0xE592427A0AEce92De3Edee1F18E0157C05861564')  # Uniswap V3 Router地址
#
# # Uniswap V2的Swap事件签名
# uniswap_v2_swap_signature = web3.keccak(text="Swap(address,uint256,uint256,uint256,uint256,address)").hex()
# print(uniswap_v2_swap_signature)
# # Uniswap V3的Swap事件签名
# uniswap_v3_swap_signature = web3.keccak(text="Swap(address,address,int256,int256,uint160,uint128,int24)").hex()
# print(uniswap_v3_swap_signature)
#
#
# # 监控Uniswap V2的Swap事件
# def monitor_uniswap_v2_swap_events(start_block, end_block):
#     for block_number in range(start_block, end_block + 1):
#         block = web3.eth.get_block(block_number, full_transactions=True)
#         for tx in block['transactions']:
#             if tx['from'] in smart_money_addresses:
#                 receipt = web3.eth.get_transaction_receipt(tx['hash'])
#
#                 # 解析Uniswap V2 Swap事件
#                 for log in receipt['logs']:
#                     print(log)
#                     if log['address'] == uniswap_v2_router_address and log['topics'][0].hex() == uniswap_v2_swap_signature:
#                         sender = web3.to_checksum_address('0x' + log['topics'][1].hex()[-40:])
#                         recipient = web3.to_checksum_address('0x' + log['topics'][5].hex()[-40:])
#                         amount0_in = int(log['data'][0:64], 16)
#                         amount1_in = int(log['data'][64:128], 16)
#                         amount0_out = int(log['data'][128:192], 16)
#                         amount1_out = int(log['data'][192:256], 16)
#
#                         print(f"Uniswap V2: 聪明钱包 {tx['from']} 执行了Swap交易")
#                         print(f"发送者: {sender}, 接收者: {recipient}")
#                         print(f"代币0输入: {amount0_in}, 代币1输入: {amount1_in}")
#                         print(f"代币0输出: {amount0_out}, 代币1输出: {amount1_out}")
#                         print(f"交易哈希: {tx['hash'].hex()}")
#
#
# # 监控Uniswap V3的Swap事件
# def monitor_uniswap_v3_swap_events(start_block, end_block):
#     for block_number in range(start_block, end_block + 1):
#         block = web3.eth.get_block(block_number, full_transactions=True)
#         for tx in block['transactions']:
#             if tx['from'] in smart_money_addresses:
#                 receipt = web3.eth.get_transaction_receipt(tx['hash'])
#
#                 # 解析Uniswap V3 Swap事件
#                 for log in receipt['logs']:
#                     if log['address'] == uniswap_v3_router_address and log['topics'][0].hex() == uniswap_v3_swap_signature:
#                         sender = web3.to_checksum_address('0x' + log['topics'][1].hex()[-40:])
#                         recipient = web3.to_checksum_address('0x' + log['topics'][2].hex()[-40:])
#                         amount0 = int(log['data'][0:64], 16)
#                         amount1 = int(log['data'][64:128], 16)
#                         sqrtPriceX96 = int(log['data'][128:192], 16)
#                         liquidity = int(log['data'][192:256], 16)
#
#                         print(f"Uniswap V3: 聪明钱包 {tx['from']} 执行了Swap交易")
#                         print(f"发送者: {sender}, 接收者: {recipient}")
#                         print(f"代币0数量: {amount0}, 代币1数量: {amount1}")
#                         print(f"当前价格(Sqrt): {sqrtPriceX96}, 流动性: {liquidity}")
#                         print(f"交易哈希: {tx['hash'].hex()}")
#
#
# # 实时监控交易
# monitor_uniswap_v2_swap_events(20818693, 20818693)