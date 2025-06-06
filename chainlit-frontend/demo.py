"""
Simple Chainlit Demo for DLS-404 Knowledge Assistant

This is a minimal demo to test the Chainlit installation and basic functionality
before running the full application.
"""
import sys
import os

# Test if we can import required modules
def test_imports():
    """Test if all required modules can be imported."""
    print("🔍 Testing imports...")
    
    try:
        import chainlit as cl
        print("✅ Chainlit imported successfully")
    except ImportError as e:
        print(f"❌ Chainlit import failed: {e}")
        print("   Run: pip install chainlit")
        return False
    
    try:
        from dotenv import load_dotenv
        print("✅ python-dotenv imported successfully")
    except ImportError as e:
        print(f"❌ python-dotenv import failed: {e}")
        return False
    
    # Test parent directory imports
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent_dir)
    
    try:
        from config.config import AZURE_OPENAI_ENDPOINT
        print("✅ Parent project config imported successfully")
    except ImportError as e:
        print(f"❌ Parent project import failed: {e}")
        print("   Make sure you're running from the chainlit-frontend directory")
        return False
    
    return True

# Simple Chainlit app for testing
try:
    import chainlit as cl
    
    @cl.on_chat_start
    async def start():
        """Simple welcome message for demo."""
        await cl.Message(
            content="""# 🧪 DLS-404 Chainlit Demo
            
This is a simple demo to test Chainlit functionality.

**If you can see this message, Chainlit is working correctly!**

Type "hello" to test the message handling.""",
            author="Demo Assistant"
        ).send()
    
    @cl.on_message
    async def main(message: cl.Message):
        """Simple echo response for demo."""
        user_input = message.content.lower()
        
        if "hello" in user_input:
            response = "👋 Hello! Chainlit is working correctly. The DLS-404 Knowledge Assistant is ready!"
        elif "test" in user_input:
            response = "✅ Test successful! All systems operational."
        else:
            response = f"You said: {message.content}\n\nThis is a demo. For the full DLS-404 Knowledge Assistant, run `chainlit run app.py -w`"
        
        await cl.Message(
            content=response,
            author="Demo Assistant"
        ).send()

except ImportError:
    # If chainlit is not available, run the test instead
    pass

if __name__ == "__main__":
    if test_imports():
        print("\n🎉 All imports successful!")
        print("\nTo run the demo:")
        print("  chainlit run demo.py -w")
        print("\nTo run the full application:")
        print("  chainlit run app.py -w")
        print("\nTo run the enhanced version:")
        print("  chainlit run enhanced_app.py -w")
    else:
        print("\n❌ Some imports failed. Please install missing dependencies:")
        print("  pip install -r requirements.txt")
        sys.exit(1) 