from abc import ABC, abstractmethod

class BaseNode(ABC):
    @abstractmethod
    def execute(self, step_config, context, browser, engine, context_soup=None, inherited_data=None):
        pass

    @staticmethod
    def validate(step_config):
        """Optional: Check if required fields exist (e.g., 'selector')"""
        return True
