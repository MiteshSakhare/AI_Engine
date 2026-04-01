#!/bin/bash

# Start Ollama service in the background
ollama serve &

# Wait for Ollama service to be ready
echo "Waiting for Ollama service to start..."
# Use 'ollama list' to check if the server is responsive
while ! ollama list > /dev/null 2>&1; do
  sleep 2
done

# Pull the required model if not already present
echo "Checking model llama3.2:3b..."
if ! ollama list | grep -q "llama3.2:3b"; then
  echo "Model not found, pulling llama3.2:3b..."
  ollama pull llama3.2:3b
else
  echo "Model already present, skipping pull."
fi

# Keep the Ollama service in the foreground
echo "Ollama setup complete, bringing service to foreground."
wait
