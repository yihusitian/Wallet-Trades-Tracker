import multiprocessing
import asyncio

from OnChain import constants as c
from SmartWalletFinder.smart_wallet_finder import SmartWalletFinder


def start_smart_wallet_find(blockchain: str):
    """
    Starts the on chain bot from the blockchain specified.

    Parameters:
        ``blockchain (str)``: name of the blockchain, e.g. ETHEREUM
    """
    smart_wallet_finder = SmartWalletFinder(blockchain=blockchain, verbose=True, lp_token_address = c.ERC20_CONTRACT['WETH'])
    asyncio.run(smart_wallet_finder.run())


def run_on_chain_bots():
    """
    Creates a proccess for each on chain bot where a RPC exists for it in OnChain/constants.py.
    """
    smart_wallet_finders_processes = []
    for blockchain in c.RPCS.keys():
        start_smart_wallet_find_process = multiprocessing.Process(target=start_smart_wallet_find, args=(blockchain,))
        smart_wallet_finders_processes.append(start_smart_wallet_find_process)
        start_smart_wallet_find_process.start()