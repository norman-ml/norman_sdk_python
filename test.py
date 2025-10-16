import asyncio
from io import BytesIO
from pathlib import Path

from PIL import Image

from norman.norman import Norman, InvocationConfig


async def main():
    # response = await Norman.signup("hadolenxx", "Dolevg1234!")
    norman = Norman(api_key="MjM4NDY0ODM0NjIzMTM0Mzc4NjM2OTkwMzExNzA5NTgyODc1NzE=_7vzGkQdcbadZitG0BwD5FtswLgahSL7amUAUbgb-awY=")

    img_path = Path("/Users/dolevgabay/Desktop/norman/sdk/img_input.jpg")

    # Run 3 invocations in a loop
    for i in range(1):
        print(f"\n🔁 Invocation #{i+1}")

        invocation_config: InvocationConfig = {
            "model_name": "my_img_model",
            "inputs": {
                "Straight Image": {
                    "source": "Path",
                    "data": img_path,
                }
            }
        }

        results = await norman.invoke(invocation_config)

        for key, value in results.items():
            print(f"🖼️ {key}: {len(value)} bytes")

            try:
                img = Image.open(BytesIO(value))
                img.show(title=f"{key} - Run {i+1}")  # show in viewer
                # Optionally save each output
                img.save(f"output_{i+1}_{key}.png")
            except Exception as e:
                print(f"❌ Could not render image '{key}': {e}")

        # Optional: Wait between runs
        # await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
