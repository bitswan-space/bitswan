"""
Configuration loading for Spark runtime.

Reads pipelines.conf in the same format as BSPump/Flink, supporting:
- [connection:Name] sections for connection settings
- [pipeline:Name:Component] sections for component config
- Environment variable expansion via ${VAR_NAME}

This module shares the same configuration format as the Flink runtime.
"""

import configparser
import os
import re
from typing import Dict, Optional


class SparkConfig:
    """Load and parse pipelines.conf for Spark runtime."""

    def __init__(self, config_path: str = "pipelines.conf"):
        self.connections: Dict[str, Dict[str, str]] = {}
        self.pipelines: Dict[str, Dict[str, str]] = {}
        self._config_path = config_path
        self._load(config_path)

    def _expand_env_vars(self, value: str) -> str:
        """Expand ${VAR_NAME} patterns with environment variables."""
        pattern = r"\$\{([^}]+)\}"

        def replacer(match):
            var_name = match.group(1)
            env_value = os.environ.get(var_name)
            if env_value is None:
                raise ValueError(
                    f"Environment variable '{var_name}' not set "
                    f"(referenced in {self._config_path})"
                )
            return env_value

        return re.sub(pattern, replacer, value)

    def _load(self, path: str) -> None:
        """Parse INI format config file."""
        if not os.path.exists(path):
            return

        config = configparser.ConfigParser(interpolation=None)
        config.read(path)

        for section in config.sections():
            section_dict = {}
            for key, value in config.items(section):
                section_dict[key] = self._expand_env_vars(value)

            if section.startswith("connection:"):
                # [connection:KafkaConnection] -> connections["KafkaConnection"]
                connection_name = section.split(":", 1)[1]
                self.connections[connection_name] = section_dict

            elif section.startswith("pipeline:"):
                # [pipeline:Name:Component] -> pipelines["Name:Component"]
                pipeline_component = section.split(":", 1)[1]
                self.pipelines[pipeline_component] = section_dict

    def get_connection(self, name: str) -> Dict[str, str]:
        """Get connection settings by name."""
        return self.connections.get(name, {})

    def get_component_config(
        self, pipeline: str, component: str
    ) -> Dict[str, str]:
        """Get component config for a specific pipeline component."""
        key = f"{pipeline}:{component}"
        return self.pipelines.get(key, {})

    def get_source_config(self, pipeline: str) -> Optional[Dict[str, str]]:
        """Find source configuration for a pipeline."""
        for key, config in self.pipelines.items():
            if key.startswith(f"{pipeline}:") and "Source" in key:
                return config
        return None

    def get_sink_config(self, pipeline: str) -> Optional[Dict[str, str]]:
        """Find sink configuration for a pipeline."""
        for key, config in self.pipelines.items():
            if key.startswith(f"{pipeline}:") and "Sink" in key:
                return config
        return None

    def get_source_connection_name(self, pipeline: str) -> Optional[str]:
        """Get the connection name for a pipeline's source."""
        for key in self.pipelines:
            if key.startswith(f"{pipeline}:") and "Source" in key:
                config = self.pipelines[key]
                return config.get("connection")
        return None

    def get_sink_connection_name(self, pipeline: str) -> Optional[str]:
        """Get the connection name for a pipeline's sink."""
        for key in self.pipelines:
            if key.startswith(f"{pipeline}:") and "Sink" in key:
                config = self.pipelines[key]
                return config.get("connection")
        return None
