from watchgod import DefaultWatcher


class SkipDefaultWatcher(DefaultWatcher):
    def __init__(self, root_path: str) -> None:
        self.ignored_dirs.add("_site")
        super().__init__(root_path)
