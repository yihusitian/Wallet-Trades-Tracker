from hexbytes import HexBytes

from OnChain import functions as f


RPCS = {
    "ETHEREUM": [
        # "https://ethereum.publicnode.com"
        "https://mainnet.infura.io/v3/cf894d2a298148e1b27782472731936e"
    ]
}

SWAPS_HEX = {
    "V2_POOL": [
        # HexBytes('0xc685db7ecb946f6dd83d43ee07d73ec25761abdc54bc77317d0b810b75ce42a9'),
        #v2 swap事件签名
        # Swap事件签名的Keccak256哈希
        #swap_event_signature_hash = web3.keccak(text="Swap(address,uint256,uint256,uint256,uint256,address)").hex()
        HexBytes('0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822')
    ],
    "V3_POOL": [
        #v3 swap事件签名
        #swap_event_signature_hash = web3.keccak(text='Swap(address,address,int256,int256,uint160,uint128,int24)').hex()
        HexBytes('0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67')
    ]
}

LINKS = {
    "SCANS": {
        "ETHEREUM": {
            "MAKER": "https://etherscan.io/address/",
            "TRANSACTION": "https://etherscan.io/tx/",
            "TOKEN": "https://etherscan.io/token/"
        }
    },
    "CHARTS": {
        "ETHEREUM": {
            "DEXSCREENER": "https://dexscreener.com/ethereum/"
        }
    }
}

UNISWAP_FACTORY_INFOS = {
    "v2": {
        "address": "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
        "abi": '''
            [
              {
                "constant": true,
                "inputs": [
                  {
                    "name": "tokenA",
                    "type": "address"
                  },
                  {
                    "name": "tokenB",
                    "type": "address"
                  }
                ],
                "name": "getPair",
                "outputs": [
                  {
                    "name": "pair",
                    "type": "address"
                  }
                ],
                "payable": false,
                "stateMutability": "view",
                "type": "function"
              }
            ]
        ''',
    },
    "v3": {
        "address": "0x1F98431c8aD98523631AE4a59f267346ea31F984",
        "abi": '''
            [
              {
                "inputs": [
                  {
                    "internalType": "address",
                    "name": "tokenA",
                    "type": "address"
                  },
                  {
                    "internalType": "address",
                    "name": "tokenB",
                    "type": "address"
                  },
                  {
                    "internalType": "uint24",
                    "name": "fee",
                    "type": "uint24"
                  }
                ],
                "name": "getPool",
                "outputs": [
                  {
                    "internalType": "address",
                    "name": "pool",
                    "type": "address"
                  }
                ],
                "stateMutability": "view",
                "type": "function"
              }
            ]
        ''',
        'feelist': [100, 500, 3000, 10000]
    },
}

ERC20_CONTRACT = {
    "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
}