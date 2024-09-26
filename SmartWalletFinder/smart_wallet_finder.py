from web3 import Web3
import asyncio
from web3.datastructures import AttributeDict
from web3.exceptions import BlockNotFound, TransactionNotFound

from web3_multi_provider import MultiProvider

from multicall import Call, Multicall

from OnChain import constants as c
from SmartWalletFinder import functions as f

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

        #某些 RPC 提供者可能不支持过滤器操作，尤其是某些云服务或较旧版本的节点
        #所以使用get_logs替换
        block_events = self.web3.eth.get_logs({
            "fromBlock": start_block,
            "toBlock": end_block,
            "address": self.get_dex_swap_pair_address(token_address),
            "topics": [
                [swap_event.hex() for sublist in [swap_events for swap_events in c.SWAPS_HEX.values()] for swap_event in sublist]
            ]
        })
        return block_events

    async def process_block_events(self):
        """
        Filters wallets addresses in the block.
        """
        meme_contracts = f.load_meme_contracts(self.blockchain)
        for meme_contract in meme_contracts:
            arr = str.split(meme_contract, ":")
            meme_contract = arr[0]
            filter_block_events = await self.filter_block_events(meme_contract, int(arr[1]), int(arr[2]))
        swaps_blockevents_to_process = [asyncio.create_task(self.process_swaps_block_events(block_event=block_event)) for block_event in filter_block_events]
        await asyncio.gather(*swaps_blockevents_to_process)


    async def process_swaps_block_events(self, block_event: AttributeDict):
        tx_hash = block_event['transactionHash'].hex()
        await self.process_swaps_transactions(tx_hash)

    async def process_swaps_transactions(self, transaction_hash: str):
        """
        Process swaps transactions.
        Parameters:
            ``transaction (AttributeDict)``: transaction dictionnary containing all the informations.
        """
        # transaction_hash = "0xc4c4702c8e706bf7011b65a26b196c51eb3fed9ca52b1b306f1b111452756e0a"
        # 获取交易信息
        transaction = self.web3.eth.get_transaction(transaction_hash)
        while True:
            try:
                tx_infos = self.web3.eth.get_transaction_receipt(transaction_hash)
                break
            # If RPC provider not synchronized
            except TransactionNotFound:
                await asyncio.sleep(1)

        from_address = transaction['from']
        # from_address = "0xf4B410A0EEE79034331353C166284130A33d8053"
        tx_logs = tx_infos['logs']

        swap_infos = {
            "CHAIN": self.blockchain,
            "MAKER_INFOS": {
                "SHORT_ADDRESS": None
            },
            "LINKS": {
                "SCAN": {
                    "MAKER": None,
                    "TRANSACTION": None
                }
            },
            "SWAPS": {}
        }
        if tx_infos['status'] == 1:
            swap_num = 1
            swap_infos['LINKS']['SCAN']['MAKER'] = c.LINKS['SCANS'][self.blockchain]['MAKER'] + from_address
            swap_infos['MAKER_INFOS']['SHORT_ADDRESS'] = from_address[:6] + "..." + from_address[-6:]
            swap_infos['LINKS']['SCAN']['TRANSACTION'] = c.LINKS['SCANS'][self.blockchain][
                                                             'TRANSACTION'] + transaction_hash
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

                            print(pool_type)
                            if pool_type == "V2_POOL":
                                amount0_in, amount1_in, amount0_out, amount1_out = [int.from_bytes(swap_data[i:i + 32], byteorder='big') for i in range(0, 128, 32)]
                                print(amount0_in, amount1_in)
                                print(amount0_out, amount1_out)

                                if amount0_in != 0:
                                    token0_amount = amount0_in
                                    token1_amount = amount1_out

                                    token0_symbol = tokens_infos['token0_symbol']
                                    token1_symbol = tokens_infos['token1_symbol']
                                    token0_decimals = tokens_infos['token0_decimals']
                                    token1_decimals = tokens_infos['token1_decimals']

                                elif amount1_in != 0:
                                    token0_amount = amount1_in
                                    token1_amount = amount0_out

                                    token0_symbol = tokens_infos['token1_symbol']
                                    token1_symbol = tokens_infos['token0_symbol']
                                    token0_decimals = tokens_infos['token1_decimals']
                                    token1_decimals = tokens_infos['token0_decimals']

                            elif pool_type == "V3_POOL":
                                def hex_to_decimal(hex_string: str):
                                    decimal = int.from_bytes(hex_string, byteorder='big')
                                    # 符号处理
                                    if decimal & (1 << 255):  # 如果最高位为1，表示是负数
                                        decimal -= 1 << 256
                                    return decimal

                                print(swap_data)
                                print(len(swap_data))
                                amount0 = hex_to_decimal(hex_string=swap_data[0:32])
                                amount1 = hex_to_decimal(hex_string=swap_data[32:64])

                                print(amount0)
                                print(amount1)

                                if amount0 > 0:
                                    token0_amount = abs(amount0)
                                    token1_amount = abs(amount1)

                                    token0_symbol = tokens_infos['token0_symbol']
                                    token1_symbol = tokens_infos['token1_symbol']
                                    token0_decimals = tokens_infos['token0_decimals']
                                    token1_decimals = tokens_infos['token1_decimals']
                                elif amount0 < 0:
                                    token0_amount = abs(amount1)
                                    token1_amount = abs(amount0)

                                    token0_symbol = tokens_infos['token1_symbol']
                                    token1_symbol = tokens_infos['token0_symbol']
                                    token0_decimals = tokens_infos['token1_decimals']
                                    token1_decimals = tokens_infos['token0_decimals']

                            swap_infos['SWAPS'][swap_num] = {
                                "SYMBOLS": {
                                    "TOKEN0": token0_symbol,
                                    "TOKEN1": token1_symbol
                                },
                                "AMOUNTS": {
                                    "TOKEN0": f.add_unit_to_bignumber(token0_amount / 10 ** token0_decimals),
                                    "TOKEN1": f.add_unit_to_bignumber(token1_amount / 10 ** token1_decimals)
                                },
                                "LINKS": {
                                    "CHART": c.LINKS['CHARTS'][self.blockchain]['DEXSCREENER'] + pool_address
                                }
                            }
                            swap_num += 1

            if self.verbose is True:
                print(
                    f"\n[{self.blockchain}] [{swap_infos['MAKER_INFOS']['SHORT_ADDRESS']}]\n> {swap_infos['LINKS']['SCAN']['TRANSACTION']}")
                for swap_id, swap_info in swap_infos['SWAPS'].items():
                    print(">", swap_id, "-", swap_info)


    async def run(self):
        """
        Creates a loop that will analyze each block created.
        """
        await self.process_block_events()
        # await self.process_swaps_transactions(transaction=None)


