# Import modules
import json


class Config:
    def __init__(self, file="/config.json"):
        self._filename = file

        with open(self._filename, "r") as f:
            self._config = json.loads(f.read())

        self._config_obj = Config.ConfigNode(self._config)

    @property
    def get(self):
        return self._config_obj

    class ConfigNode:
        def __init__(self, config):
            for k, v in config.items():
                if isinstance(k, (list, tuple)):
                    setattr(
                        self,
                        k,
                        [Config.ConfigNode(x) if isinstance(x, dict) else x for x in v],
                    )
                else:
                    setattr(self, k, Config.ConfigNode(v) if isinstance(v, dict) else v)
