"""
This module contains the Planner component.
The Planner is responsible for defining target websites, categories,
and any throttling or legality checks.
"""

class Planner:
    """
    Manages the list of target sites and their configurations.
    """
    def __init__(self, config_path=None):
        """
        Initializes the Planner.
        Args:
            config_path (str, optional): Path to a configuration file.
                                         Defaults to None.
        """
        self.targets = []
        if config_path:
            self.load_config(config_path)
        else:
            # Default targets if no config is provided
            self.targets = [
                {"url": "http://example.com/news", "category": "general", "enabled": True},
                {"url": "http://anotherexample.com/business", "category": "business", "enabled": True},
                {"url": "http://example.org/technology", "category": "technology", "enabled": False}
            ]

    def load_config(self, config_path):
        """
        Loads target configurations from a file.
        (This can be implemented later)
        Args:
            config_path (str): Path to the configuration file.
        """
        # In a real implementation, this would load from a JSON, YAML, or DB
        print(f"Loading configuration from {config_path} (not implemented yet)")
        # For now, we'll just add a dummy target to simulate loading
        self.targets.append({"url": "http://configexample.com/sports", "category": "sports", "enabled": True})
        pass

    def get_targets(self):
        """
        Returns the list of enabled targets to be scraped.
        Each target can be a dictionary with URL, category, and other metadata.
        Returns:
            list: A list of enabled target configurations.
        """
        return [target for target in self.targets if target.get("enabled", True)]

if __name__ == '__main__':
    # Example usage

    # Planner with default targets
    print("Planner with default targets:")
    planner_default = Planner()
    targets_default = planner_default.get_targets()
    if targets_default:
        for target in targets_default:
            print(f"  Target URL: {target['url']}, Category: {target['category']}")
    else:
        print("  No targets found.")

    print("\nPlanner with a config file (simulated loading):")
    # Planner with a (dummy) config path
    planner_config = Planner(config_path="dummy_config.json")
    targets_config = planner_config.get_targets()
    if targets_config:
        for target in targets_config:
            print(f"  Target URL: {target['url']}, Category: {target['category']}")
    else:
        print("  No targets found.")

    # Example of how one might add a new target (though this should be managed via config ideally)
    print("\nManually adding a new target to default planner:")
    new_target = {"url": "http://newsite.com/politics", "category": "politics", "enabled": True}
    planner_default.targets.append(new_target) # Directly appending for example purposes
    targets_updated = planner_default.get_targets()
    if targets_updated:
        for target in targets_updated:
            print(f"  Target URL: {target['url']}, Category: {target['category']}")
    else:
        print("  No targets found.")
