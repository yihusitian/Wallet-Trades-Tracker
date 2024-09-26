import json

from web3 import Web3
import asyncio
from web3.datastructures import AttributeDict
from web3.exceptions import BlockNotFound, TransactionNotFound

from web3_multi_provider import MultiProvider

from multicall import Call, Multicall

from OnChain import constants as c
from SmartWalletFinder import functions as f
from datetime import datetime
from SmartWalletFinder import data_analyize

class SmartWalletFinder():

    def __init__(self, blockchain: str, verbose: bool, lp_token_address: str):
        self.blockchain = blockchain
        self.verbose = verbose
        self.web3 = Web3(MultiProvider(c.RPCS[blockchain]))
        self.lp_token_address = lp_token_address
        if self.verbose is True:
            print(f"[SMART_WALLET_FINDER] [{self.blockchain}] [STARTED]")

    async def get_block_number(self):
        """
        Returns blockchain block number.
        """
        return self.web3.eth.get_block_number()

    async def get_block_transactions(self):
        """
        Returns block transactions.
        """
        while True:
            try:
                block = self.web3.eth.get_block(self.block_number, full_transactions=True)
                transactions = block['transactions']
                return transactions
            # If RPC provider not synchronized
            except BlockNotFound:
                pass

    def get_dex_swap_pair_address(self, token_address: str):
        pair_addresses = []
        uniswap_v2_pair_address = f.getUniswapV2PairAddress(self.web3, self.lp_token_address, token_address)
        uniswap_v3_pair_address = f.getUniswapV3PairAddress(self.web3, self.lp_token_address, token_address)
        if uniswap_v2_pair_address:
            pair_addresses.append(uniswap_v2_pair_address)
        if uniswap_v3_pair_address:
            for v3_pair_address in uniswap_v3_pair_address:
                pair_addresses.append(v3_pair_address)
        return pair_addresses


    async def filter_block_events(self, token_address: str, start_block: int, end_block: int) -> list:
        # 创建过滤器
        # history_filter = self.web3.eth.filter({
        #     "fromBlock": start_block,
        #     "toBlock": end_block,
        #     "address": self.get_dex_swap_pair_address(token_address),
        #     "topics": [
        #         [swap_event.hex() for sublist in [swap_events for swap_events in c.SWAPS_HEX.values()] for swap_event in sublist]
        #     ]
        # })
        # # 查询历史事件
        # block_events = history_filter.get_all_entries()
        if end_block == 0:
            end_block = self.web3.eth.block_number
        print(f"查询区块{start_block}-{end_block}的历史事件")
        #某些 RPC 提供者可能不支持过滤器操作，尤其是某些云服务或较旧版本的节点
        #所以使用get_logs替换
        result = []
        while start_block <= end_block:
            temp_end_block = start_block + 100
            if temp_end_block >= end_block:
                temp_end_block = end_block
            block_events = self.web3.eth.get_logs({
                "fromBlock": start_block,
                "toBlock": temp_end_block,
                "address": self.get_dex_swap_pair_address(token_address),
                "topics": [
                    [swap_event.hex() for sublist in [swap_events for swap_events in c.SWAPS_HEX.values()] for swap_event in sublist]
                ]
            })
            print(f"查询区块{start_block}-{temp_end_block}的历史事件")
            print(f"过滤查询出区块日志事件有{len(block_events)}个")
            result += block_events
            start_block = temp_end_block

        print(f"累计查询出区块日志事件有{len(result)}个")
        return result

    def get_event_tx_ids(self, block_events: list) -> set:
        # 使用集合来提取不重复的交易哈希
        unique_tx_hashes = set()
        for log in block_events:
            tx_hash = log['transactionHash'].hex()
            unique_tx_hashes.add(tx_hash)
        return unique_tx_hashes

    async def process_block_events(self):
        """
        Filters wallets addresses in the block.
        """
        meme_contracts = f.load_meme_contracts(self.blockchain)
        for meme_contract in meme_contracts:
            arr = str.split(meme_contract, ":")
            meme_contract_address = arr[0]
            filter_block_events = await self.filter_block_events(meme_contract_address, int(arr[1]), int(arr[2]))
            event_tx_ids = self.get_event_tx_ids(filter_block_events)
            swap_data_infos = [await self.process_swaps_transactions(transaction_hash=tx_id, meme_contract_address=meme_contract_address) for tx_id in event_tx_ids]
            if swap_data_infos and len(swap_data_infos) > 0:
                data_analyize.append_token_swap_data(swap_data_infos, swap_data_infos[0]['token0_symbol'], swap_data_infos[0]['token1_symbol'])


    async def process_swaps_transactions(self, transaction_hash: str, meme_contract_address: str):
        """
        Process swaps transactions.
        Parameters:
            ``transaction (AttributeDict)``: transaction dictionnary containing all the informations.
        """
        # transaction_hash = "0xc4c4702c8e706bf7011b65a26b196c51eb3fed9ca52b1b306f1b111452756e0a"
        # 获取交易信息
        transaction = self.web3.eth.get_transaction(transaction_hash)

        # print(transaction)
        while True:
            try:
                tx_infos = self.web3.eth.get_transaction_receipt(transaction_hash)
                break
            # If RPC provider not synchronized
            except TransactionNotFound:
                await asyncio.sleep(1)

        # 获取区块信息
        block = self.web3.eth.get_block(tx_infos['blockNumber'])

        # 获取区块时间戳并转化为可读时间格式
        block_timestamp = block['timestamp']
        transaction_time = datetime.utcfromtimestamp(block_timestamp).strftime('%Y-%m-%d %H:%M:%S')

        from_address = transaction['from']
        # from_address = "0xf4B410A0EEE79034331353C166284130A33d8053"
        tx_logs = tx_infos['logs']

        swap_infos = {
            "CHAIN": self.blockchain,
            "MAKER_INFOS": {
                "WALLET_ADDRESS": None
            },
            "SWAPS": {},
            "TX_TIME": transaction_time
        }
        result = {
            "wallet_address": from_address,
            "tx_time": transaction_time,
            "token0_symbol": None,
            "token1_symbol": None,
            "token0_amount": 0,
            "token1_amount": 0,
            "direction": None #1买入 0卖出
        }
        if tx_infos['status'] == 1:
            swap_num = 1
            swap_infos['MAKER_INFOS']['WALLET_ADDRESS'] = from_address
            for tx_log in tx_logs:
                for tx_log_topic in tx_log['topics']:
                    for pool_type, pool_values in c.SWAPS_HEX.items():
                        if tx_log_topic in pool_values:
                            swap_data = tx_log['data']
                            pool_address = tx_log['address']
                            queries = [
                                Call(pool_address, 'token0()(address)', [['token0_address', None]]),
                                Call(pool_address, 'token1()(address)', [['token1_address', None]]),
                            ]
                            # 池子币对儿
                            pool_tokens_infos = await Multicall(queries, _w3=self.web3, require_success=True).coroutine()
                            token0_address = Web3.to_checksum_address(pool_tokens_infos['token0_address'])
                            token1_address = Web3.to_checksum_address(pool_tokens_infos['token1_address'])

                            queries = [
                                Call(token0_address, 'symbol()(string)', [['token0_symbol', None]]),
                                Call(token1_address, 'symbol()(string)', [['token1_symbol', None]]),
                                Call(token0_address, 'decimals()(uint8)', [['token0_decimals', None]]),
                                Call(token1_address, 'decimals()(uint8)', [['token1_decimals', None]])
                            ]
                            # {'token0_symbol': 'WETH', 'token1_symbol': 'MARS', 'token0_decimals': 18, 'token1_decimals': 9}
                            tokens_infos = await Multicall(queries, _w3=self.web3, require_success=True).coroutine()
                            if pool_type == "V2_POOL":
                                amount0_in, amount1_in, amount0_out, amount1_out = [int.from_bytes(swap_data[i:i + 32], byteorder='big') for i in range(0, 128, 32)]
                                if amount0_in != 0:
                                    token0_amount = amount0_in
                                    token1_amount = amount1_out

                                    token0_symbol = tokens_infos['token0_symbol']
                                    token1_symbol = tokens_infos['token1_symbol']
                                    token0_contract_address = token0_address
                                    token1_contract_address = token1_address
                                    token0_decimals = tokens_infos['token0_decimals']
                                    token1_decimals = tokens_infos['token1_decimals']

                                elif amount1_in != 0:
                                    token0_amount = amount1_in
                                    token1_amount = amount0_out

                                    token0_symbol = tokens_infos['token1_symbol']
                                    token1_symbol = tokens_infos['token0_symbol']
                                    token0_contract_address = token1_address
                                    token1_contract_address = token0_address
                                    token0_decimals = tokens_infos['token1_decimals']
                                    token1_decimals = tokens_infos['token0_decimals']

                            elif pool_type == "V3_POOL":
                                def hex_to_decimal(hex_string: str):
                                    decimal = int.from_bytes(hex_string, byteorder='big')
                                    # 符号处理
                                    if decimal & (1 << 255):  # 如果最高位为1，表示是负数
                                        decimal -= 1 << 256
                                    return decimal

                                amount0 = hex_to_decimal(hex_string=swap_data[0:32])
                                amount1 = hex_to_decimal(hex_string=swap_data[32:64])
                                if amount0 > 0:
                                    token0_amount = abs(amount0)
                                    token1_amount = abs(amount1)

                                    token0_symbol = tokens_infos['token0_symbol']
                                    token1_symbol = tokens_infos['token1_symbol']
                                    token0_contract_address = token0_address
                                    token1_contract_address = token1_address
                                    token0_decimals = tokens_infos['token0_decimals']
                                    token1_decimals = tokens_infos['token1_decimals']
                                elif amount0 < 0:
                                    token0_amount = abs(amount1)
                                    token1_amount = abs(amount0)

                                    token0_symbol = tokens_infos['token1_symbol']
                                    token1_symbol = tokens_infos['token0_symbol']
                                    token0_contract_address = token1_address
                                    token1_contract_address = token0_address
                                    token0_decimals = tokens_infos['token1_decimals']
                                    token1_decimals = tokens_infos['token0_decimals']

                            token0_final_amount = token0_amount / 10 ** token0_decimals
                            token1_final_amount = token1_amount / 10 ** token1_decimals
                            swap_infos['SWAPS'][swap_num] = {
                                "SYMBOLS": {
                                    "TOKEN0": token0_symbol,
                                    "TOKEN1": token1_symbol,
                                    "TOKEN0_ADDRESS": token0_contract_address,
                                    "TOKEN1_ADDRESS": token1_contract_address,
                                },
                                "AMOUNTS": {
                                    "TOKEN0": token0_final_amount,
                                    "TOKEN1": token1_final_amount
                                },
                            }
                            swap_num += 1

                            if token0_contract_address.lower() == self.lp_token_address.lower() and token1_contract_address.lower() == meme_contract_address.lower():
                                result['token0_symbol'] = token0_symbol
                                result['token1_symbol'] = token1_symbol
                                result['token0_amount'] += token0_final_amount
                                result['token1_amount'] += token1_final_amount
                                result['direction'] = 1

                            if token0_contract_address.lower() == meme_contract_address.lower() and token1_contract_address.lower() == self.lp_token_address.lower():
                                result['token0_symbol'] = token0_symbol
                                result['token1_symbol'] = token1_symbol
                                result['token0_amount'] += token0_final_amount
                                result['token1_amount'] += token1_final_amount
                                result['direction'] = 0

            if self.verbose is True:
                print(f"\n[{self.blockchain}] [{swap_infos['MAKER_INFOS']['WALLET_ADDRESS']}]\n")
                for swap_id, swap_info in swap_infos['SWAPS'].items():
                    print(">", swap_id, "-", swap_info)
        return result


    async def run(self):
        """
        Creates a loop that will analyze each block created.
        """
        await self.process_block_events()
        # await self.process_swaps_transactions(transaction=None)


