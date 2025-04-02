# Creating Custom Ollama Models from Modelfiles

This guide explains how to create custom Ollama models from modelfiles for the Spring Test Sequence Generator application.

## What is a Modelfile?

A Modelfile is a configuration file that tells Ollama how to create a custom model. It includes:

- The base model to use
- Custom parameters for the model
- System prompts and instructions
- Optional template variables

## Basic Steps to Create a Model

1. Create a modelfile (e.g., `spring-assistant-complete.modelfile`)
2. Run the Ollama create command
3. Update your application to use the new model

## Modelfile Structure

A typical modelfile includes:

```
FROM <base-model>

# Parameters
PARAMETER temperature <value>
PARAMETER num_ctx <value>
PARAMETER num_thread <value>
PARAMETER num_gpu <value>

# System prompt
SYSTEM """
Your custom system prompt goes here...
"""
```

## Creating a Model from a Modelfile

To create a model from a modelfile, use the following command:

```bash
ollama create <model-name> -f <modelfile-path>
```

For example:

```bash
ollama create spring-assistant-complete -f spring-assistant-complete.modelfile
```

This command will:
1. Read the modelfile
2. Download the base model if needed
3. Apply your custom configurations
4. Create a new model with your specified name

## Example: Creating the Spring Assistant Model

Our `spring-assistant-complete` model is created from a modelfile that:

1. Uses the `qwen2.5-coder:3b` model as a base
2. Sets optimal parameters for our use case
3. Includes a comprehensive system prompt with instructions for generating spring test sequences
4. Ensures the model provides proper JSON output format

## Verifying Your Model

After creating your model, you can verify it was created successfully using:

```bash
ollama list
```

You should see your model in the list with details about its size and when it was created.

## Using Your Model

To use your custom model in the Spring Test Sequence Generator app:

1. Update the `DEFAULT_OLLAMA_MODEL` in `utils/constants.py`
2. Update the `DEFAULT_OLLAMA_MODEL` in `utils/ollama_client.py` if needed
3. Restart the application

## Testing Your Model

You can test your model directly with the Ollama CLI:

```bash
ollama run <model-name> "Your test prompt here"
```

For example:

```bash
ollama run spring-assistant-complete "Generate a test sequence for a compression spring with free length 58mm and set points at 40mm (23.6N), 33mm (34.14N), and 28mm (42.36N)."
```

## Troubleshooting

If your model creation fails:
- Check for syntax errors in your modelfile
- Ensure you have enough disk space for the model
- Verify that the base model is available
- Check the Ollama logs for specific error messages

If your model produces unexpected outputs:
- Review and refine the system prompt in your modelfile
- Adjust the temperature parameter (lower for more deterministic outputs)
- Ensure your prompts are clear and follow the format expected by the model 