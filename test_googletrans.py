import asyncio
from googletrans import Translator
import httpcore

async def main():
    try:
        translator = Translator()
        result = await translator.translate("Hello", dest="hi")
        print(f"✅ Success: {result.text}")
    except AttributeError as e:
        print(f"❌ AttributeError: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
