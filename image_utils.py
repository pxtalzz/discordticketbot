from PIL import Image, ImageDraw, ImageFont, ImageFilter
import aiohttp
import io
from typing import Optional
from datetime import datetime

async def create_stats_image(
    user,
    banner_url: Optional[str],
    avatar_url: str,
    username: str,
    created_at: datetime,
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
                    
                    aspect = banner.width / banner.height
                    target_aspect = width / height
                    
                    if aspect > target_aspect:
                        new_height = height
                        new_width = int(aspect * new_height)
                    else:
                        new_width = width
                        new_height = int(new_width / aspect)
                    
                    banner = banner.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    banner = banner.filter(ImageFilter.GaussianBlur(radius=10))
                    
                    x = (new_width - width) // 2
                    y = (new_height - height) // 2
                    banner = banner.crop((x, y, x + width, y + height))
                    
                    img.paste(banner, (0, 0))
    else:
        async with aiohttp.ClientSession() as session:
            async with session.get(avatar_url) as resp:
                if resp.status == 200:
                    avatar_data = await resp.read()
                    avatar_bg = Image.open(io.BytesIO(avatar_data))
                    
                    aspect = avatar_bg.width / avatar_bg.height
                    target_aspect = width / height
                    
                    if aspect > target_aspect:
                        new_height = height
                        new_width = int(aspect * new_height)
                    else:
                        new_width = width
                        new_height = int(new_width / aspect)
                    
                    avatar_bg = avatar_bg.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    avatar_bg = avatar_bg.filter(ImageFilter.GaussianBlur(radius=15))
                    
                    x = (new_width - width) // 2
                    y = (new_height - height) // 2
                    avatar_bg = avatar_bg.crop((x, y, x + width, y + height))
                    
                    img.paste(avatar_bg, (0, 0))
    
    async with aiohttp.ClientSession() as session:
        async with session.get(avatar_url) as resp:
            if resp.status == 200:
                avatar_data = await resp.read()
                avatar = Image.open(io.BytesIO(avatar_data))
                avatar = avatar.resize((200, 200), Image.Resampling.LANCZOS)
                
                mask = Image.new('L', (200, 200), 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.ellipse((0, 0, 200, 200), fill=255)
                
                img.paste(avatar, (30, 51), mask)
    
    draw = ImageDraw.Draw(img)
    
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    draw.text((width // 2, 40), username, fill=(255, 255, 255), font=font_large, anchor="mt")
    
    discord_join = created_at.strftime("%m/%d/%Y")
    draw.text((width - 20, 20), f"Discord: {discord_join}", fill=(200, 200, 200), font=font_small, anchor="rt")
    
    output = io.BytesIO()
    img.save(output, format='PNG')
    output.seek(0)
    return output
