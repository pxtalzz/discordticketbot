from PIL import Image, ImageDraw, ImageFont, ImageFilter
import aiohttp
import io
from typing import Optional

async def create_stats_image(
    user,
    banner_url: Optional[str],
    avatar_url: str,
    badges: list = []
) -> io.BytesIO:
    width = 885
    height = 303
    
    img = Image.new('RGB', (width, height), color=(0, 0, 0))
    
    if banner_url:
        async with aiohttp.ClientSession() as session:
            async with session.get(banner_url) as resp:
                if resp.status == 200:
                    banner_data = await resp.read()
                    banner = Image.open(io.BytesIO(banner_data))
                    banner = banner.resize((width, height))
                    banner = banner.filter(ImageFilter.GaussianBlur(radius=10))
                    img.paste(banner, (0, 0))
    else:
        async with aiohttp.ClientSession() as session:
            async with session.get(avatar_url) as resp:
                if resp.status == 200:
                    avatar_data = await resp.read()
                    avatar_bg = Image.open(io.BytesIO(avatar_data))
                    avatar_bg = avatar_bg.resize((width, height))
                    avatar_bg = avatar_bg.filter(ImageFilter.GaussianBlur(radius=15))
                    img.paste(avatar_bg, (0, 0))
    
    async with aiohttp.ClientSession() as session:
        async with session.get(avatar_url) as resp:
            if resp.status == 200:
                avatar_data = await resp.read()
                avatar = Image.open(io.BytesIO(avatar_data))
                avatar = avatar.resize((150, 150))
                
                mask = Image.new('L', (150, 150), 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.ellipse((0, 0, 150, 150), fill=255)
                
                img.paste(avatar, (30, 76), mask)
    
    output = io.BytesIO()
    img.save(output, format='PNG')
    output.seek(0)
    return output
