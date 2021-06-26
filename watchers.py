from os import DirEntry

from watchgod import AllWatcher, DefaultWatcher


class SkipDefaultWatcher(DefaultWatcher):
    def __init__(self, root_path: str) -> None:
        self.ignored_dirs.add("_site")
        super().__init__(root_path)


class SkipIgnoreWatcher(AllWatcher):
    def __init__(self, root_path: str, should_ignore=None) -> None:
        self.should_ignore = should_ignore
        super().__init__(root_path)

    def should_watch_dir(self, entry: DirEntry) -> bool:
        return not self.should_ignore(entry.path)

    def should_watch_file(self, entry: DirEntry) -> bool:
        return not self.should_ignore(entry.path)
