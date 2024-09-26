from web3 import Web3
import asyncio
from web3.datastructures import AttributeDict
from web3.exceptions import BlockNotFound, TransactionNotFound

from web3_multi_provider import MultiProvider

from multicall import Call, Multicall

from OnChain import constants as c
from SmartWalletFinder import functions as f

class SmartWalletFinder():

    def __init__(self, blockchain: str, verbose: bool):
        self.blockchain = blockchain
        self.verbose = verbose
        self.web3 = Web3(MultiProvider(c.RPCS[blockchain]))
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

    async def filter_block_events(self, start_block: int, end_block: int, token_address: str) -> list:
        self.web3.eth.filter({
            "fromBlock": start_block,
            "toBlock": end_block,
            "topics": [
                [swap_event.hex() for sublist in [swap_events for swap_events in c.SWAPS_HEX.values()] for swap_event in sublist]
            ]
    })

    async def process_transactions(self):
        """
        Filters wallets addresses in the block.
        """
        meme_contracts = f.load_meme_contracts()
        for meme_contract in meme_contracts:


        filtered_transactions = [
            transaction for transaction in self.transactions
            if transaction.get('from', '').lower() in [meme_contract[:str.index(meme_contract, ":")].lower() for meme_contract in z]
        ]
        swaps_transactions_to_process = [asyncio.create_task(self.process_swaps_transactions(transaction=transaction))
                                         for transaction in filtered_transactions]
        await asyncio.gather(*swaps_transactions_to_process)
