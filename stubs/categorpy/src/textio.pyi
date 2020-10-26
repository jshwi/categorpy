import os
from typing import Any, Optional, Union, Dict, Callable, Tuple, List


class TextIO:
    def __init__(self, path: Any, _object: Optional[Any] = ..., **kwargs: Any) -> None:
        self.path: Union[bytes, str, os.PathLike] = ...
        self.ispath: bool = ...
        self.output: str = ...
        self.object: Dict[str, Any] = ...
        self.method: str = ...
        self.args: Tuple[str, ...] = ...
        self.sort: bool = ...
    def _passive_dedupe(self, content: List[str]) -> List[str]: ...
    def _output(self, content: str) -> None: ...
    def read_to_list(self) -> List[str]: ...
    def _execute(self, obj: str) -> None: ...
    def _compile_string(self, content: List[str]) -> None: ...
    def _write_file(self, mode: str) -> None: ...
    def _mode(self, mode: str) -> str: ...
    def write_list(self, content: List[str]) -> None: ...
    def write_json(self) -> None: ...
    def write_json_setting(self, key: str, val: str) -> None: ...
    def append(self, content: List[str]) -> None: ...
    def write(self, content: str) -> None: ...
    def read(self) -> None: ...
    def read_bytes(self) -> None: ...
    def read_json(self) -> None: ...
    def append_json_array(self, *args: Tuple[str, Dict[str, Union[Union[int, str], Any]]]) -> None: ...

def pygment_print(string: str) -> None: ...
def record_hist(history: TextIO, url: str) -> None: ...
def initialize_paths_file(paths: Union[bytes, str, os.PathLike]) -> List[str]: ...
