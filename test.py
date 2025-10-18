import asyncio
from io import BytesIO
from pathlib import Path

from PIL import Image

from norman.norman import Norman, InvocationConfig
from norman_core.clients.http_client import HttpClient
from norman_core.services.authenticate import Authenticate


async def main():
    # async with HttpClient() as http_client:
    #     await Authenticate.login.login_default(http_client, "23846483462313437863699031170958287571")

    # response = await Norman.signup("hadolenxx5", "Dolevg1234!")
    norman = Norman(api_key="ZGsorQTN82NtOsZJJXa3Tib2T4FHgdrLU-Y5QmaAFcGWD4WB--Z-jeg_6N7zclQ1WjL0gM6r9yO7rD5KAwOwpWB-YLJH0T9vMpTmCbTIbHjs0nQC")

    img_path = Path("/Users/dolevgabay/Desktop/norman/sdk/img_input.jpg")

    # Run 3 invocations in a loop
    for i in range(1):
        print(f"\n🔁 Invocation #{i+1}")

        invocation_config: InvocationConfig = {
            "model_name": "my_img_model2",
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
