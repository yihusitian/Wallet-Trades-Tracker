from typing import Union
import os
from web3 import Web3
from OnChain import constants as c

"""
    加载meme合约文件
"""
def load_meme_contracts(blockchain: str) -> list:
    with open(os.path.join(os.getcwd(), 'meme_contract.txt'), 'r') as meme_contract_file:
        meme_contract_lines = [line.strip() for line in meme_contract_file.readlines() if line.startswith(blockchain)]
        meme_contracts = []
        for meme_contract_line in meme_contract_lines:
            meme_contracts.append(meme_contract_line.replace(f"{blockchain}:", ""))
    return meme_contracts

"""
    Uniswap V2 池合约地址
"""
def getUniswapV2PairAddress(web3: Web3, tokenAaddress:str, tokenBaddress:str) -> str:
    # Uniswap V2 工厂信息
    uniswap_v2_factory_info = c.UNISWAP_FACTORY_INFOS['v2']
    # Uniswap V2 工厂合约地址
    uniswap_v2_factory_address = Web3.to_checksum_address(uniswap_v2_factory_info['address'])
    # Uniswap V2 工厂合约的ABI (部分示例)
    uniswap_v2_factory_abi = uniswap_v2_factory_info['abi']
    # 初始化工厂合约实例
    factory_contract = web3.eth.contract(address=uniswap_v2_factory_address, abi=uniswap_v2_factory_abi)
    # 指定要查询的两个代币的地址 (比如 WETH 和 USDC)
    # tokenA = Web3.to_checksum_address('0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2')  # WETH
    # tokenB = Web3.to_checksum_address('0xc3D2B3e23855001508e460A6dbE9f9e3116201aF')  # MARS
    tokenA = Web3.to_checksum_address(tokenAaddress)
    tokenB = Web3.to_checksum_address(tokenBaddress)
    # 调用getPair方法获取池合约地址
    pair_address = factory_contract.functions.getPair(tokenA, tokenB).call()
    print(f"Uniswap V2 Pool Address: {pair_address}")
    return pair_address

"""
    Uniswap V3 池合约地址
"""
def getUniswapV3PairAddress(web3: Web3, tokenAaddress:str, tokenBaddress:str) -> list:
    # Uniswap V3 工厂信息
    uniswap_v3_factory_info = c.UNISWAP_FACTORY_INFOS['v3']
    # Uniswap V3 工厂合约地址
    uniswap_v3_factory_address = Web3.to_checksum_address(uniswap_v3_factory_info['address'])
    # Uniswap V3 工厂合约ABI (部分示例)
    uniswap_v3_factory_abi = uniswap_v3_factory_info['abi']
    # Uniswap V3 手续费率列表
    uniswap_v3_factory_feelist = uniswap_v3_factory_info['feelist']
    # 初始化工厂合约实例
    v3_factory_contract = web3.eth.contract(address=uniswap_v3_factory_address, abi=uniswap_v3_factory_abi)
    # 指定代币地址和费用级别 (WETH, USDC, 0.3%)
    tokenA = Web3.to_checksum_address(tokenAaddress)
    tokenB = Web3.to_checksum_address(tokenBaddress)
    # 获取Uniswap V3池合约地址
    pool_addresses = [pool_address for pool_address in [v3_factory_contract.functions.getPool(tokenA, tokenB, fee).call() for fee in uniswap_v3_factory_feelist] if pool_address != '0x0000000000000000000000000000000000000000']
    print(f"Uniswap V3 Pool Addresses: {pool_addresses}")
    return pool_addresses