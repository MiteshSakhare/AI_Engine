#!/bin/bash

# Start Ollama service in the background
ollama serve &

# Wait for Ollama service to be ready
echo "Waiting for Ollama service to start..."
while ! curl -s http://localhost:11434/api/tags > /dev/null; do
  sleep 1
done

# Pull the required model
echo "Pulling model llama3.2:3b..."
ollama pull llama3.2:3b

# Keep the Ollama service in the foreground
echo "Ollama setup complete, bringing service to foreground."
wait
