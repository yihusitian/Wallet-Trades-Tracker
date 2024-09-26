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
        uniswap_v2_pair_address = f.getUniswapV2PairAddress(self.lp_token_address, token_address)
        uniswap_v3_pair_address = f.getUniswapV3PairAddress(self.lp_token_address, token_address)
        if uniswap_v2_pair_address:
            pair_addresses.append(pair_addresses)
        if uniswap_v3_pair_address:
            for v3_pair_address in uniswap_v3_pair_address:
                pair_addresses.append(v3_pair_address)
        return pair_addresses


    async def filter_block_events(self, token_address: str, start_block: int, end_block: int) -> list:
        return self.web3.eth.filter({
            "fromBlock": start_block,
            "toBlock": end_block,
            "address": self.get_dex_swap_pair_address(token_address),
            "topics": [
                [swap_event.hex() for sublist in [swap_events for swap_events in c.SWAPS_HEX.values()] for swap_event in sublist]
            ]
        })

    async def process_block_events(self):
        """
        Filters wallets addresses in the block.
        """
        meme_contracts = f.load_meme_contracts()
        for meme_contract in meme_contracts:
            arr = str.split(meme_contract, ":")
            meme_contract = arr[0]
            filter_block_events = await self.filter_block_events(meme_contract, int(arr[1]), int(arr[2]))
        swaps_blockevents_to_process = [asyncio.create_task(self.process_swaps_block_events(block_event=block_event)) for block_event in filter_block_events]
        await asyncio.gather(*swaps_blockevents_to_process)


    async def process_swaps_transactions(self, block_event: AttributeDict):
        print(block_event)
        tx_hash = block_event['transactionHash'].hex()
        print(tx_hash)




    async def run(self):
        """
        Creates a loop that will analyze each block created.
        """
        await self.process_block_events()
        # await self.process_swaps_transactions(transaction=None)


