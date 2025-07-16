#!/bin/bash

echo "🌟 Setting up Tellor Layer Profitability Checker..."

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "⬇️  Installing Python dependencies..."
pip install -r requirements.txt

# Create config file from example
if [ ! -f config.yaml ]; then
    echo "⚙️  Creating config file..."
    cp config_example.yaml config.yaml
    echo "✅ Config file created! Please edit config.yaml with your layerd path."
    echo "💡 Run 'which layerd' to find your layerd path."
else
    echo "⚙️  Config file already exists."
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit config.yaml with your layerd path:"
echo "   which layerd"
echo "2. Run the profitability checker:"
echo "   source venv/bin/activate"
echo "   python src/main.py" 