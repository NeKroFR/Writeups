import hashlib

class Rng:
    def __init__(self, seed: bytes):
        self.state = hashlib.sha256(b"RNG_CHAIN" + seed).digest()

    def get(self) -> bytes:
        res = hashlib.sha256(b"RNG_OUT" + self.state).digest()
        self.state = hashlib.sha256(b"RNG_CHAIN" + self.state).digest()
        return res
