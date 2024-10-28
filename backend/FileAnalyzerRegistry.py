from Enums.FileType import FileType
from Files.BPUFileAnalyzer import BPUFileAnalyzer
from Files.CCAPFileAnalyzer import CCAPFileAnalyzer
from Files.CCTPFileAnalyser import CCTPFileAnalyzer
from Files.MAINFileAnalyzer import MAINFileAnalyzer
from Files.RCFileAnalyzer import RCFileAnalyzer
from BaseFileAnalyzer import BaseFileAnalyzer

class FileAnalyzerRegistry:
    _instances = {}

    @classmethod
    def initialize_registry(cls):
        cls._instances = {
            FileType.RC: RCFileAnalyzer(),
            FileType.CCAP: CCAPFileAnalyzer(),
            FileType.CCTP: CCTPFileAnalyzer(),
            FileType.BPU: BPUFileAnalyzer(),
            FileType.MAIN: MAINFileAnalyzer(),
        }

    @classmethod
    def get_analyzer(cls, file_name: str) -> BaseFileAnalyzer:
        file_name_lower = file_name.lower()

        for file_type, analyzer in cls._instances.items():
            if any(alias in file_name_lower for alias in file_type.value):
                return analyzer
        return None

    @classmethod
    def _get_analyzer_class(cls, file_type: FileType):
        registry = {
            FileType.RC: RCFileAnalyzer,
            FileType.CCAP: CCAPFileAnalyzer,
            FileType.CCTP: CCTPFileAnalyzer,
            FileType.BPU: BPUFileAnalyzer,
            FileType.MAIN: MAINFileAnalyzer,
        }
        return registry.get(file_type)
