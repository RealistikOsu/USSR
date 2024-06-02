from __future__ import annotations

import glob
import os


class Path:
    def __init__(self, file_path: str) -> None:
        self._path = file_path

    @staticmethod
    def cwd() -> Path:
        return Path(os.getcwd())

    def __str__(self) -> str:
        return self._path

    def __truediv__(self, other_path: str | Path) -> Path:
        if isinstance(other_path, str):
            return Path(os.path.join(self._path, other_path))

        # not sure if this even makes sense lol?
        return Path(os.path.join(self._path, other_path._path))

    def exists(self) -> bool:
        return os.path.exists(self._path)

    def read_bytes(self) -> bytes:
        if not self.exists():
            raise FileNotFoundError

        with open(self._path, "rb") as f:
            file_bytes = f.read()

        return file_bytes

    def read_text(self) -> str:
        if not self.exists():
            raise FileNotFoundError

        with open(self._path) as f:
            file_contents = f.read()

        return file_contents

    def write_bytes(self, content: bytes) -> None:
        with open(self._path, "wb") as f:
            f.write(content)

    def write_text(self, content: str) -> None:
        with open(self._path, "w") as f:
            f.write(content)

    def mkdir(
        self,
        mode: int = 0o777,
        parents: bool = False,
        exist_ok: bool = False,
    ) -> None:
        if self.exists():
            if not exist_ok:
                raise FileExistsError

            return

        if parents:
            os.makedirs(self._path, mode)
        else:
            os.mkdir(self._path, mode)

    def glob(self, pattern: str, recursive: bool = False) -> list[Path]:
        file_paths = glob.glob(os.path.join(self._path, pattern), recursive=recursive)
        if not file_paths:
            return []

        return [Path(file_path) for file_path in file_paths]

    def rglob(self, pattern: str) -> list[Path]:
        return self.glob(f"**/{pattern}", recursive=True)
