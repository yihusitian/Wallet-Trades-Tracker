import asyncio

from web3 import Web3
from web3.datastructures import AttributeDict
from web3.exceptions import BlockNotFound, TransactionNotFound

from web3_multi_provider import MultiProvider

from multicall import Call, Multicall


from OnChain import constants as c
from OnChain import functions as f

from Discord.functions import send_discord_webhook
from Telegram.functions import send_telegram_message
from CompanyWechat.functions import send_company_wechat_message


class OnChainBot():
    
    
    def __init__(self, blockchain: str, verbose: bool):
        """
        Initializes the on chain bot instance.
        
        Parameters:
            ``blockchain (str)``: blockchain where on chain bot needs to run.\n
            ``verbose (bool)``: Enable/Disable the verbose (on chain bot started, block creation, swap found)
        """
        
        self.blockchain = blockchain
        self.verbose = verbose
        self.web3 = Web3(MultiProvider(c.RPCS[blockchain]))
        if self.verbose is True:
            print(f"[ONCHAINBOT] [{self.blockchain}] [STARTED]")
    

    async def relayer(self, swap_infos: dict):
        """
        Executes different actions when a swap is found.
        
        Parameters:
            ``swap_infos (dict)``: dictionnary containing all the informations from the swap, e.g. tokens names, amounts swapped, transaction link...
        """
        
        # await send_discord_webhook(swap_infos=swap_infos)
        # await send_telegram_message(swap_infos=swap_infos)
        await send_company_wechat_message(swap_infos=swap_infos)
        
        
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
    
    
    async def process_transactions(self):
        """
        Filters wallets addresses in the block.
        """
        
        wallets = f.load_wallets(blockchain=self.blockchain)
        filtered_transactions = [
            transaction for transaction in self.transactions
            if transaction.get('from', '').lower() in [wallet.lower() for wallet in wallets]
        ]
        swaps_transactions_to_process = [asyncio.create_task(self.process_swaps_transactions(transaction=transaction)) for transaction in filtered_transactions]
        await asyncio.gather(*swaps_transactions_to_process)
        
        
    async def process_swaps_transactions(self, transaction: AttributeDict):
        """
        Process swaps transactions.
        
        Parameters:
            ``transaction (AttributeDict)``: transaction dictionnary containing all the informations.
        """
        
        transaction_hash = transaction.hash.hex()
        # transaction_hash = "0xc4c4702c8e706bf7011b65a26b196c51eb3fed9ca52b1b306f1b111452756e0a"
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
        
        is_tx_swap = False
        if tx_infos['status'] == 1:
            swap_num = 1
            swap_infos['LINKS']['SCAN']['MAKER'] = c.LINKS['SCANS'][self.blockchain]['MAKER'] + from_address
            swap_infos['MAKER_INFOS']['SHORT_ADDRESS'] = from_address[:6] + "..." + from_address[-6:]
            swap_infos['LINKS']['SCAN']['TRANSACTION'] = c.LINKS['SCANS'][self.blockchain]['TRANSACTION'] + transaction_hash
            for tx_log in tx_logs:
                for tx_log_topic in tx_log['topics']:
                    for pool_type, pool_values in c.SWAPS_HEX.items():
                        if tx_log_topic in pool_values:
                            is_tx_swap = True
                            swap_data = tx_log['data']

                            pool_address = tx_log['address']
                            queries = [
                                Call(pool_address, 'token0()(address)', [['token0_address', None]]),
                                Call(pool_address, 'token1()(address)', [['token1_address', None]]),
                            ]
                            #池子币对儿
                            pool_tokens_infos = await Multicall(queries, _w3=self.web3, require_success=True).coroutine()
                            token0_address = Web3.to_checksum_address(pool_tokens_infos['token0_address'])
                            token1_address = Web3.to_checksum_address(pool_tokens_infos['token1_address'])
                            
                            queries = [
                                Call(token0_address, 'symbol()(string)', [['token0_symbol', None]]),
                                Call(token1_address, 'symbol()(string)', [['token1_symbol', None]]),
                                Call(token0_address, 'decimals()(uint8)', [['token0_decimals', None]]),
                                Call(token1_address, 'decimals()(uint8)', [['token1_decimals', None]])
                            ]
                            #{'token0_symbol': 'WETH', 'token1_symbol': 'MARS', 'token0_decimals': 18, 'token1_decimals': 9}
                            tokens_infos = await Multicall(queries, _w3=self.web3, require_success=True).coroutine()

                            print(pool_type)
                            if pool_type == "V2_POOL":
                                amount0_in, amount1_in, amount0_out, amount1_out = [int.from_bytes(swap_data[i:i+32], byteorder='big') for i in range(0, 128, 32)]
                                # Convert 32-byte chunks to integers directly using `int.from_bytes()`
                                # amount0_in = int.from_bytes(swap_data[0:32], byteorder='big')
                                # amount1_in = int.from_bytes(swap_data[32:64], byteorder='big')
                                # amount0_out = int.from_bytes(swap_data[64:96], byteorder='big')
                                # amount1_out = int.from_bytes(swap_data[96:128], byteorder='big')
                                print(amount0_in, amount1_in)
                                print(amount0_out, amount1_out)
                                
                                if amount0_in != 0:
                                    token0_amount = amount0_in
                                    token1_amount = amount1_out
                                    
                                    token0_symbol = tokens_infos['token0_symbol']
                                    token1_symbol = tokens_infos['token1_symbol']
                                    token0_decimals = tokens_infos['token0_decimals']
                                    token1_decimals = tokens_infos['token1_decimals']
                                    
                                elif amount1_in !=0:
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
                                    "TOKEN0": f.add_unit_to_bignumber(token0_amount/10**token0_decimals),
                                    "TOKEN1": f.add_unit_to_bignumber(token1_amount/10**token1_decimals)
                                },
                                "LINKS": {
                                    "CHART": c.LINKS['CHARTS'][self.blockchain]['DEXSCREENER'] + pool_address
                                }
                            }
                            
                            swap_num += 1
                            
            if self.verbose is True:
                print(f"\n[{self.blockchain}] [{swap_infos['MAKER_INFOS']['SHORT_ADDRESS']}]\n> {swap_infos['LINKS']['SCAN']['TRANSACTION']}")
                for swap_id, swap_info in swap_infos['SWAPS'].items():
                    print(">", swap_id, "-", swap_info)
            
            if is_tx_swap is True:
                await self.relayer(swap_infos=swap_infos)
      
                             
    async def run(self):
        """
        Creates a loop that will analyze each block created.
        """
        latest_block_number = await self.get_block_number()

        while True:
            current_block_number = await self.get_block_number()

            if current_block_number > latest_block_number:
                if self.verbose is True:
                    print(f"\n[{self.blockchain}] [BLOCK {current_block_number}]")
                latest_block_number = current_block_number
                self.block_number = current_block_number
                self.transactions = await self.get_block_transactions()
                await self.process_transactions()
        # await self.process_swaps_transactions(transaction=None)
