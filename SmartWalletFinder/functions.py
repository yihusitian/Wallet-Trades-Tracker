from typing import Union
import os

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

