from enum import Enum

class FileType(Enum):
    RC = ["rc"]
    CCAP = ["ccap"]
    CCTP = ["cctp", "cstp"]  # "CCTP" peut être détecté par "cctp" ou "cstp"
    BPU = ["bpu"]
    MAIN = ["main"]
    MAIN2 = ["main2"]