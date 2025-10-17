from PIL import Image, ImageDraw, ImageFont, ImageFilter
import aiohttp
import io
from typing import Optional

async def create_stats_image(
    user,
    banner_url: Optional[str],
    avatar_url: str,
    username: str,
    join_date: Optional[str],
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
                avatar = avatar.resize((250, 250), Image.Resampling.LANCZOS)
                
                mask = Image.new('L', (250, 250), 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.ellipse((0, 0, 250, 250), fill=255)
                
                img.paste(avatar, (30, 26), mask)
    
    draw = ImageDraw.Draw(img)
    
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    except IOError:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    username_bbox = draw.textbbox((0, 0), username, font=font_large)
    username_width = username_bbox[2] - username_bbox[0]
    
    avatar_right = 280
    left_margin = 25
    
    min_text_x_for_left = avatar_right + left_margin + (username_width / 2)
    center_x = width / 2
    
    text_x = max(center_x, min_text_x_for_left)
    
    draw.text((int(text_x), 120), username, fill=(255, 255, 255), font=font_large, anchor="mt")
    
    if join_date and join_date != 'N/A':
        if '<t:' in join_date:
            join_text = join_date.split(':')[1].split(':')[0]
            try:
                from datetime import datetime
                timestamp = int(join_text)
                dt = datetime.fromtimestamp(timestamp)
                join_text = f"{dt.strftime('%b %d, %Y')}"
            except (ValueError, IndexError):
                join_text = "N/A"
        else:
            join_text = join_date
        
        text_bbox = draw.textbbox((0, 0), join_text, font=font_small)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        padding = 15
        circle_x = width - text_width - padding * 2 - 20
        circle_y = height - text_height - padding * 2 - 20
        circle_width = text_width + padding * 2
        circle_height = text_height + padding * 2
        
        draw.rounded_rectangle(
            ((circle_x, circle_y), (circle_x + circle_width, circle_y + circle_height)),
            radius=20,
            fill=(40, 40, 40, 200)
        )
        
        text_x = circle_x + padding
        text_y = circle_y + padding
        draw.text((text_x, text_y), join_text, fill=(255, 255, 255), font=font_small)
    
    output = io.BytesIO()
    img.save(output, format='PNG')
    output.seek(0)
    return output
