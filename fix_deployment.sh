#!/bin/bash

# Fix Azure OpenAI deployment configuration
# The deployment was incorrectly set to "gpt-40" but should be "gpt-4o"

echo "🔧 Fixing Azure OpenAI deployment configuration..."

# Export the correct deployment name
export AZURE_OPENAI_COMPLETION_DEPLOYMENT="gpt-4o"

echo "✅ Updated AZURE_OPENAI_COMPLETION_DEPLOYMENT to: $AZURE_OPENAI_COMPLETION_DEPLOYMENT"

# Update the environment for current session
echo "export AZURE_OPENAI_COMPLETION_DEPLOYMENT=\"gpt-4o\"" >> ~/.bashrc
echo "export AZURE_OPENAI_COMPLETION_DEPLOYMENT=\"gpt-4o\"" >> ~/.zshrc

echo "📝 Updated shell configuration files"
echo "🚀 To apply changes permanently, restart your terminal or run: source ~/.zshrc"

# Show current configuration
echo ""
echo "Current Azure OpenAI Configuration:"
echo "AZURE_OPENAI_ENDPOINT: $AZURE_OPENAI_ENDPOINT"
echo "AZURE_OPENAI_COMPLETION_DEPLOYMENT: $AZURE_OPENAI_COMPLETION_DEPLOYMENT"
echo "AZURE_OPENAI_EMBEDDING_DEPLOYMENT: $AZURE_OPENAI_EMBEDDING_DEPLOYMENT" 