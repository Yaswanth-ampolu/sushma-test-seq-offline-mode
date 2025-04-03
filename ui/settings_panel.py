# Look for places where model/provider names are displayed:
# - Dropdown options
# - Radio buttons
# - Labels
# - Descriptions

# For example, if there's model selection code like:
def _populate_model_dropdown(self):
    # Add Together.ai models to dropdown
    # Replace display names only, not internal model identifiers
    if "together" in self.available_providers:
        for model in self.available_models.get("together", []):
            display_name = model.get("display_name", "")
            if "Together" in display_name:
                display_name = display_name.replace("Together.ai", "FTS.ai")
                model["display_name"] = display_name
            self.model_dropdown.addItem(display_name, model["id"])

# Or text in labels:
provider_label = QLabel("FTS.ai API Key:")
model_description = "FTS.ai Falcon model (fast, good for code generation)" 