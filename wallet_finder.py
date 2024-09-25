from SmartWalletFinder import functions as f


if __name__ == '__main__':
    meme_contracts = f.load_meme_contracts("ETHEREUM")
    for meme_contract in meme_contracts:
        print(meme_contract)
        print(meme_contract[:str.index(meme_contract, ":")])
